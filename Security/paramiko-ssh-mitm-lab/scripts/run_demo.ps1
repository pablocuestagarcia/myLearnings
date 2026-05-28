# Demo end-to-end del lab paramiko AutoAddPolicy MITM (Windows PowerShell).
# Uso: desde la raiz del lab -> .\scripts\run_demo.ps1
#      o directamente:        powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1

$ErrorActionPreference = "Continue"

# Posicionarse en la raiz del lab (un nivel por encima de scripts/)
$labRoot = Split-Path -Parent $PSScriptRoot
Set-Location $labRoot

$base  = @("-f", "docker-compose.yml")
$legit = @("-f", "docker-compose.client-legit.yml")
$evil  = @("-f", "docker-compose.client-evil.yml")

function Separator($msg) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $msg
    Write-Host "============================================================"
}

Separator "Paso 0: build + arranque de los dos servidores"
docker compose @base build
docker compose @base up -d legit-server evil-server
Write-Host "Esperando 6s a que sshd este escuchando..."
Start-Sleep -Seconds 6

Separator "Paso 1: capturar host key del LEGITIMO (172.28.0.10) y guardarla como sokrates-vm"
docker compose @base @legit run --rm -T client `
    bash -c 'ssh-keyscan -t ed25519 172.28.0.10 2>/dev/null | sed "s|^172.28.0.10|sokrates-vm|" > /work/known_host.pub && echo "--- known_host.pub ---" && cat /work/known_host.pub'

Separator "Escenario A | trafico LEGITIMO + cliente VULNERABLE"
Write-Host "Esperado: lee 'datos confidenciales del pharma pipeline'."
docker compose @base @legit run --rm -T client python /work/client/client_vulnerable.py

Separator "Escenario B | MITM + cliente VULNERABLE  <-- EL ATAQUE"
Write-Host "Esperado: AutoAddPolicy() acepta sin avisar, manda la password al atacante."
docker compose @base @evil run --rm -T client python /work/client/client_vulnerable.py
Write-Host ""
Write-Host "--- /var/log/stolen.log en evil-server (credenciales capturadas) ---"
docker compose @base exec -T evil-server cat /var/log/stolen.log

Separator "Escenario C | MITM + cliente SEGURO  <-- DEFENSA"
Write-Host "Esperado: BadHostKeyException o 'not found in known_hosts'. NO se envia la password."
$before = (docker compose @base exec -T evil-server sh -c "wc -l < /var/log/stolen.log").Trim()
docker compose @base @evil run --rm -T client python /work/client/client_secure.py
$after = (docker compose @base exec -T evil-server sh -c "wc -l < /var/log/stolen.log").Trim()
Write-Host ""
Write-Host "Lineas en stolen.log antes=$before, despues=$after"
if ($before -eq $after) {
    Write-Host "OK: paramiko aborto antes de auth, no hay nuevas credenciales robadas."
} else {
    Write-Host "MAL: se ha registrado una linea nueva en stolen.log."
}

Separator "Escenario D | trafico LEGITIMO + cliente SEGURO"
Write-Host "Esperado: lee el fichero, demuestra que la version segura no rompe el caso bueno."
docker compose @base @legit run --rm -T client python /work/client/client_secure.py

Separator "Fin. Para parar todo: docker compose down -v"
