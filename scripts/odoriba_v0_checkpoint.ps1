param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Json
)

function Invoke-CommandAndReport {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [bool]$SuppressOutput = $false
    )

    try {
        if ($SuppressOutput) {
            & $FilePath @Arguments *> $null
        }
        else {
            & $FilePath @Arguments
        }

        if ($LASTEXITCODE -eq 0) {
            return $true
        }

        return $false
    }
    catch {
        return $false
    }
}

$repoExists = Test-Path $RepoRoot
if (-not $repoExists) {
    Write-Output "repo_root_not_found"
    exit 1
}

$repoRootResolved = (Resolve-Path $RepoRoot).Path
Set-Location $repoRootResolved

$testsDir = 'tests'
$smokePath = Join-Path $repoRootResolved 'scripts\odoriba_v0_smoke.ps1'
$helperPath = 'scripts/validate_odoriba_v0_result_fixtures.py'
$skipPytest = $env:ODORIBA_CHECKPOINT_RECURSION_GUARD -eq '1'

$commandArgs = @{
    SuppressOutput = $Json.IsPresent
}

$okPytest = if ($skipPytest) {
    $true
} else {
    Invoke-CommandAndReport -Name 'pytest_passed' -FilePath 'py' -Arguments @('-3', '-B', '-m', 'pytest', $testsDir, '-q') @commandArgs
}
$okFixtureValidation = Invoke-CommandAndReport -Name 'fixture_validation_passed' -FilePath 'py' -Arguments @('-3', '-B', $helperPath) @commandArgs
$okFixtureSchema = Invoke-CommandAndReport -Name 'fixture_schema_validation_passed' -FilePath 'py' -Arguments @('-3', '-B', $helperPath, 'schema') @commandArgs
$okPositiveSmoke = Invoke-CommandAndReport -Name 'positive_smoke_passed' -FilePath 'powershell' -Arguments @(
    '-ExecutionPolicy',
    'Bypass',
    '-Command',
    "& '$smokePath' -Mode positive -Translator mock_view_v0"
) @commandArgs
$okNegativeSmoke = Invoke-CommandAndReport -Name 'negative_smoke_passed' -FilePath 'powershell' -Arguments @(
    '-ExecutionPolicy',
    'Bypass',
    '-Command',
    "& '$smokePath' -Mode negative -Translator mock_view_v0"
) @commandArgs

if ($Json) {
    $checkpointPassed = $okPytest -and $okFixtureValidation -and $okFixtureSchema -and $okPositiveSmoke -and $okNegativeSmoke
    $output = [ordered]@{
        schema = 'odoriba_v0_checkpoint_v1'
        status = if ($checkpointPassed) { 'passed' } else { 'failed' }
        pytest_passed = $okPytest
        fixture_validation_passed = $okFixtureValidation
        fixture_schema_validation_passed = $okFixtureSchema
        positive_smoke_passed = $okPositiveSmoke
        negative_smoke_passed = $okNegativeSmoke
        repo_rename = $false
        cross_repo_integration = $false
        core_changed = $false
        smoke_script_changed = $false
        checkpoint_passed = $checkpointPassed
        boundary = @{
            repo_rename = $false
            cross_repo_integration = $false
            core_unchanged = $true
            smoke_script_unchanged = $true
        }
    }

    $output | ConvertTo-Json -Depth 4
    if ($checkpointPassed) {
        exit 0
    }

    exit 1
}

if ($okPytest) { Write-Output 'pytest_passed=passed' } else { Write-Output 'pytest_passed=failed' }
if ($okFixtureValidation) { Write-Output 'fixture_validation_passed=passed' } else { Write-Output 'fixture_validation_passed=failed' }
if ($okFixtureSchema) { Write-Output 'fixture_schema_validation_passed=passed' } else { Write-Output 'fixture_schema_validation_passed=failed' }
if ($okPositiveSmoke) { Write-Output 'positive_smoke_passed=passed' } else { Write-Output 'positive_smoke_passed=failed' }
if ($okNegativeSmoke) { Write-Output 'negative_smoke_passed=passed' } else { Write-Output 'negative_smoke_passed=failed' }

Write-Output 'repo_rename=false'
Write-Output 'cross_repo_integration=false'

if ($okPytest -and $okFixtureValidation -and $okFixtureSchema -and $okPositiveSmoke -and $okNegativeSmoke) {
    Write-Output 'core_changed=false'
    Write-Output 'smoke_script_changed=false'
    Write-Output 'checkpoint_passed=true'
    exit 0
}

Write-Output 'core_changed=false'
Write-Output 'smoke_script_changed=false'
Write-Output 'checkpoint_passed=false'
exit 1
