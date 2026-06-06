param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

function Invoke-CommandAndReport {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments
    )

    try {
        $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -Wait -PassThru
        if ($process.ExitCode -eq 0) {
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
$testsDir = Join-Path $repoRootResolved 'tests'
$scriptsDir = Join-Path $repoRootResolved 'scripts'
$smokePath = Join-Path $scriptsDir 'odoriba_v0_smoke.ps1'
$helperPath = Join-Path $scriptsDir 'validate_odoriba_v0_result_fixtures.py'

$okPytest = Invoke-CommandAndReport -Name 'pytest_passed' -FilePath 'py' -Arguments @('-3', '-B', '-m', 'pytest', $testsDir, '-q')
$okFixtureValidation = Invoke-CommandAndReport -Name 'fixture_validation_passed' -FilePath 'py' -Arguments @('-3', '-B', $helperPath)
$okFixtureSchema = Invoke-CommandAndReport -Name 'fixture_schema_validation_passed' -FilePath 'py' -Arguments @('-3', '-B', $helperPath, 'schema')
$okPositiveSmoke = Invoke-CommandAndReport -Name 'positive_smoke_passed' -FilePath 'powershell' -Arguments @(
    '-ExecutionPolicy', 'Bypass', '-File', $smokePath, '-Mode', 'positive', '-Translator', 'mock_view_v0'
)
$okNegativeSmoke = Invoke-CommandAndReport -Name 'negative_smoke_passed' -FilePath 'powershell' -Arguments @(
    '-ExecutionPolicy', 'Bypass', '-File', $smokePath, '-Mode', 'negative', '-Translator', 'mock_view_v0'
)

if ($okPytest) { Write-Output 'pytest_passed=passed' } else { Write-Output 'pytest_passed=failed' }
if ($okFixtureValidation) { Write-Output 'fixture_validation_passed=passed' } else { Write-Output 'fixture_validation_passed=failed' }
if ($okFixtureSchema) { Write-Output 'fixture_schema_validation_passed=passed' } else { Write-Output 'fixture_schema_validation_passed=failed' }
if ($okPositiveSmoke) { Write-Output 'positive_smoke_passed=passed' } else { Write-Output 'positive_smoke_passed=failed' }
if ($okNegativeSmoke) { Write-Output 'negative_smoke_passed=passed' } else { Write-Output 'negative_smoke_passed=failed' }

Write-Output 'repo_rename=false'
Write-Output 'cross_repo_integration=false'

if ($okPytest -and $okFixtureValidation -and $okFixtureSchema -and $okPositiveSmoke -and $okNegativeSmoke) {
    Write-Output 'checkpoint_passed=true'
    exit 0
}

Write-Output 'checkpoint_passed=false'
exit 1
