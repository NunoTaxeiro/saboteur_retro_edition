param(
    [string]$Stamp = (Get-Date -Format 'yyyyMMddHHmmss'),
    [string]$PythonExe = 'python'
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$sourceGame = Join-Path $rootDir 'saboteur.py'
$webBuildSrcDir = Join-Path $rootDir 'web_build_src'
$generatedWebDir = Join-Path $webBuildSrcDir 'build\web'
$publicWebDir = Join-Path $rootDir 'web\public\saboteur-web'
$rootBuildWebDir = Join-Path $rootDir 'build\web'
$reactAppFile = Join-Path $rootDir 'web\src\App.jsx'
$packageBase = "web_build_src_$Stamp"
$legacyPackageBase = 'saboteur_retro_edition'

function Update-FileText {
    param(
        [string]$Path,
        [scriptblock]$Transform
    )

    $original = Get-Content -Path $Path -Raw
    $updated = & $Transform $original
    Set-Content -Path $Path -Value $updated -NoNewline
}

function Replace-RequiredText {
    param(
        [string]$Content,
        [string]$OldText,
        [string]$NewText,
        [string]$Label
    )

    if (-not $Content.Contains($OldText)) {
        throw "Wrapper patch failed for $Label"
    }

    return $Content.Replace($OldText, $NewText)
}

function Replace-RequiredRegex {
    param(
        [string]$Content,
        [string]$Pattern,
        [string]$Replacement,
        [string]$Label
    )

    $updated = [regex]::Replace($Content, $Pattern, $Replacement, 1)
    if ($updated -eq $Content) {
        throw "Wrapper patch failed for $Label"
    }

    return $updated
}

function New-PatchedWrapper {
    param(
        [string]$TemplatePath,
        [string]$PackageName
    )

    $content = Get-Content -Path $TemplatePath -Raw

    if (-not $content.StartsWith('<!DOCTYPE html>')) {
        $content = "<!DOCTYPE html>`r`n$content"
    }

    $content = Replace-RequiredText -Content $content -OldText '<html lang="en-us"><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module id="site" data-python="python3.12" data-LINES=42 data-COLUMNS=132 data-os="vtx,snd,gui" async defer>' -NewText '<html lang="en-us"><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module id="site" data-python="python3.12" data-LINES=42 data-COLUMNS=132 data-os="vtx,snd,gui">' -Label 'site script tag'
    $content = Replace-RequiredText -Content $content -OldText 'Loading web_build_src from web_build_src.apk' -NewText "Loading $PackageName from $PackageName.apk" -Label 'loading banner'
    $content = Replace-RequiredText -Content $content -OldText '    Title   : web_build_src' -NewText "    Title   : $PackageName" -Label 'title banner'
    $content = Replace-RequiredText -Content $content -OldText '    Folder  : web_build_src' -NewText "    Folder  : $PackageName" -Label 'folder banner'
    $content = Replace-RequiredText -Content $content -OldText '    bundle = "web_build_src"' -NewText "    bundle = `"$PackageName`"" -Label 'bundle name'
    $content = Replace-RequiredText -Content $content -OldText '    archive : "web_build_src",' -NewText "    archive : `"$PackageName`"," -Label 'archive config'
    $content = Replace-RequiredText -Content $content -OldText '    <title>web_build_src</title>' -NewText "    <title>$PackageName</title>" -Label 'document title'
    $content = Replace-RequiredText -Content $content -OldText '    appdir.mkdir()' -NewText '    appdir.mkdir(parents=True, exist_ok=True)' -Label 'appdir mkdir'
    $content = Replace-RequiredText -Content $content -OldText '    ume_block : 1,' -NewText '    ume_block : 0,' -Label 'ume block'
    $content = Replace-RequiredText -Content $content -OldText '    <script src="https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js"></script>' -NewText '    <script src="browserfs.min.js"></script>' -Label 'browserfs script'
    $content = Replace-RequiredText -Content $content -OldText '/*           display: none; */' -NewText '            display: none;' -Label 'infobox default visibility'

    $originalUnpackBlock = @"
    # unpack filesystem from compressed archive into work dir
    if platform.window.location.host.find('.itch.zone')>0:
        import zipfile
        async with platform.fopen("web_build_src.apk", "rb") as archive:
            with zipfile.ZipFile(archive) as zip_ref:
                zip_ref.extractall(appdir.as_posix())
    else:
        import tarfile
        async with platform.fopen("web_build_src.tar.gz", "rb") as archive:
            tar = tarfile.open(fileobj=archive, mode="r:gz")
            tar.extractall(path=appdir.as_posix(), filter='tar')
            tar.close()

    # preloader will change to work dir and prepend it to sys.path
"@
    $patchedUnpackBlock = @"
    # unpack filesystem from lightweight APK (zip) to avoid tar extraction stalls
    import zipfile
    async with platform.fopen("$PackageName.apk", "rb") as archive:
        with zipfile.ZipFile(archive) as zip_ref:
            zip_ref.extractall(appdir.as_posix())

    # preloader will change to work dir and prepend it to sys.path
"@
    $content = Replace-RequiredText -Content $content -OldText $originalUnpackBlock -NewText $patchedUnpackBlock -Label 'filesystem unpack block'

    $originalEntrypointBlock = @"
    main = appdir / "assets" / "main.py"

    # TODO: test for window.webkitAudioContext and block aio loop until gesture if accessing media manager play
"@
    $patchedEntrypointBlock = @"
    main = appdir / "assets" / "main.py"
    if not main.is_file():
        for candidate in (
            appdir / "assets" / "saboteur.py",
            appdir / "assets" / "web_build_src" / "main.py",
            appdir / "assets" / "web_build_src" / "saboteur.py",
        ):
            if candidate.is_file():
                main = candidate
                break

    # TODO: test for window.webkitAudioContext and block aio loop until gesture if accessing media manager play
"@
    $content = Replace-RequiredText -Content $content -OldText $originalEntrypointBlock -NewText $patchedEntrypointBlock -Label 'entrypoint fallback block'

    $originalUiCallbackBlock = @"

    def ui_callback(pkg):
        platform.window.infobox.innerText = f"installing {pkg}"

    await shell.source(main, callback=ui_callback)

    # if you don't reach that step
    # your main.py has an infinite sync loop somewhere !

    platform.window.infobox.style.display = "none"
    platform.window.config.gui_divider = 1
    platform.window.window_resize()
    print("default.tmpl: done")
"@
    $patchedUiCallbackBlock = @"

    def ui_callback(pkg):
        platform.window.infobox.innerText = f"installing {pkg}"

    platform.window.infobox.style.display = "none"
    platform.window.config.gui_divider = 1
    platform.window.window_resize()

    await shell.source(main, callback=ui_callback)

    # if you don't reach that step
    # your main.py has an infinite sync loop somewhere !
    print("default.tmpl: done")
"@
    $content = Replace-RequiredText -Content $content -OldText $originalUiCallbackBlock -NewText $patchedUiCallbackBlock -Label 'ui callback block'

    $originalCustomOnloadBlock = @"
    async function custom_onload(debug_hidden) {
        // this is called before anything python is loaded
        // make your js customization here
        console.log(__FILE__, "custom_onload")

        pyconsole.hidden = debug_hidden
        system.hidden = debug_hidden
        transfer.hidden = debug_hidden
        info.hidden = debug_hidden
        box.hidden =  debug_hidden

        show_infobox()
    }
"@
    $patchedCustomOnloadBlock = @"
    async function custom_onload(debug_hidden) {
        pyconsole.hidden = debug_hidden
        system.hidden = debug_hidden
        transfer.hidden = debug_hidden
        info.hidden = debug_hidden
        box.hidden = debug_hidden
    }
"@
    $content = Replace-RequiredText -Content $content -OldText $originalCustomOnloadBlock -NewText $patchedCustomOnloadBlock -Label 'custom_onload block'

    $originalCustomPrerunBlock = @"
    function custom_prerun(){
        // no python main and no (MEMFS + VFS) yet.
        console.log(__FILE__, "custom_prerun")

    }

    function custom_postrun(){
        // python main and no VFS filesystem yet.
        console.log(__FILE__, "custom_postrun")

    }
"@
    $patchedCustomPrerunBlock = @"
    function custom_prerun(){
    }

    function custom_postrun(){
    }
"@
    $content = Replace-RequiredText -Content $content -OldText $originalCustomPrerunBlock -NewText $patchedCustomPrerunBlock -Label 'custom prerun/postrun blocks'

    return $content
}

Write-Host "Building web package $packageBase"

Copy-Item -Path $sourceGame -Destination (Join-Path $webBuildSrcDir 'main.py') -Force
Copy-Item -Path $sourceGame -Destination (Join-Path $webBuildSrcDir 'saboteur.py') -Force

Push-Location $webBuildSrcDir
$env:PYTHONUTF8 = '1'
& $PythonExe -m pygbag --build main.py
Pop-Location

$generatedIndex = Join-Path $generatedWebDir 'index.html'
$generatedApk = Join-Path $generatedWebDir 'web_build_src.apk'
$generatedTar = Join-Path $generatedWebDir 'web_build_src.tar.gz'
$generatedIcon = Join-Path $generatedWebDir 'favicon.png'

foreach ($dir in @($publicWebDir, $rootBuildWebDir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Remove-Item -Path (Join-Path $dir 'web_build_src_*.apk') -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $dir 'web_build_src_*.tar.gz') -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $dir "$legacyPackageBase.apk") -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $dir "$legacyPackageBase.tar.gz") -Force -ErrorAction SilentlyContinue
    Copy-Item -Path $generatedApk -Destination (Join-Path $dir "$packageBase.apk") -Force
    Copy-Item -Path $generatedTar -Destination (Join-Path $dir "$packageBase.tar.gz") -Force
    Copy-Item -Path $generatedApk -Destination (Join-Path $dir "$legacyPackageBase.apk") -Force
    Copy-Item -Path $generatedTar -Destination (Join-Path $dir "$legacyPackageBase.tar.gz") -Force
    Copy-Item -Path $generatedIcon -Destination (Join-Path $dir 'favicon.png') -Force
}

$browserFsPublic = Join-Path $publicWebDir 'browserfs.min.js'
$browserFsBuild = Join-Path $rootBuildWebDir 'browserfs.min.js'
if (Test-Path $browserFsPublic) {
    Copy-Item -Path $browserFsPublic -Destination $browserFsBuild -Force
}

$patchedWrapper = New-PatchedWrapper -TemplatePath $generatedIndex -PackageName $packageBase
Set-Content -Path (Join-Path $publicWebDir 'index.html') -Value $patchedWrapper -NoNewline
Set-Content -Path (Join-Path $rootBuildWebDir 'index.html') -Value $patchedWrapper -NoNewline

Update-FileText -Path $reactAppFile -Transform {
    param($text)
    [regex]::Replace($text, 'const buildStamp = "[^"]+";', "const buildStamp = `"$packageBase`";", 1)
}

Write-Host "Published web package: $packageBase"
