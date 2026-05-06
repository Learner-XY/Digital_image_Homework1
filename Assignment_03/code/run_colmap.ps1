param(
    [string]$Colmap = "colmap",
    [string]$ImagePath = "data/images",
    [string]$OutputPath = "outputs/colmap",
    [string]$WorkPath = "outputs/colmap_runtime",
    [switch]$CpuOnly
)

$ErrorActionPreference = "Continue"

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
New-Item -ItemType Directory -Force -Path $WorkPath | Out-Null
$SparsePath = Join-Path $WorkPath "sparse"
$DensePath = Join-Path $WorkPath "dense"
$DatabasePath = Join-Path $WorkPath "database.db"
$LogPath = Join-Path $OutputPath "colmap_log.txt"
New-Item -ItemType Directory -Force -Path $SparsePath | Out-Null
New-Item -ItemType Directory -Force -Path $DensePath | Out-Null

$gpuFlag = "1"
if ($CpuOnly) { $gpuFlag = "0" }

function Run-Step {
    param([string]$Name, [scriptblock]$Command)
    "=== $Name ===" | Tee-Object -FilePath $LogPath -Append
    & $Command 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Run-Step "Feature Extraction" {
    & $Colmap feature_extractor `
        --database_path $DatabasePath `
        --image_path $ImagePath `
        --ImageReader.camera_model PINHOLE `
        --ImageReader.single_camera 1 `
        --FeatureExtraction.use_gpu $gpuFlag
}

Run-Step "Feature Matching" {
    & $Colmap exhaustive_matcher `
        --database_path $DatabasePath `
        --FeatureMatching.use_gpu $gpuFlag
}

Run-Step "Sparse Reconstruction" {
    & $Colmap mapper `
        --database_path $DatabasePath `
        --image_path $ImagePath `
        --output_path $SparsePath
}

if (Test-Path (Join-Path $SparsePath "0")) {
    Run-Step "Export Sparse PLY" {
        & $Colmap model_converter `
            --input_path (Join-Path $SparsePath "0") `
            --output_path (Join-Path $OutputPath "sparse.ply") `
            --output_type PLY
    }
}

try {
    Run-Step "Image Undistortion" {
        & $Colmap image_undistorter `
            --image_path $ImagePath `
            --input_path (Join-Path $SparsePath "0") `
            --output_path $DensePath
    }

    Run-Step "Patch Match Stereo" {
        & $Colmap patch_match_stereo `
            --workspace_path $DensePath `
            --PatchMatchStereo.geom_consistency true
    }

    Run-Step "Stereo Fusion" {
        & $Colmap stereo_fusion `
            --workspace_path $DensePath `
            --output_path (Join-Path $OutputPath "fused.ply")
    }
    "DENSE_STATUS=success" | Tee-Object -FilePath (Join-Path $OutputPath "summary.txt")
} catch {
    "DENSE_STATUS=failed" | Tee-Object -FilePath (Join-Path $OutputPath "summary.txt")
    ("ERROR=" + $_.Exception.Message) | Tee-Object -FilePath (Join-Path $OutputPath "summary.txt") -Append
    throw
}
