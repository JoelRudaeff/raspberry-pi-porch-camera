# Enables Remote Desktop on this PC so it can be reached ONLY from the Raspberry Pi
# (<PI_LAN_IP>) - in practice only from the iPhone through the WireGuard VPN, and only
# while "Remote Desktop over VPN" is on in Home Assistant.
#
# - Network Level Authentication stays required (Windows sign-in before any session starts).
# - Only the two "User Mode" RDP firewall rules are enabled, each limited to the Pi's address.
#   The "Shadow" rule (watching someone else's session) stays off.
#
# Asks for administrator permission (UAC) when run normally.

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$PSCommandPath`""
    exit
}

$ErrorActionPreference = 'Stop'
$pi = '<PI_LAN_IP>'

Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1

foreach ($rule in 'RemoteDesktop-UserMode-In-TCP', 'RemoteDesktop-UserMode-In-UDP') {
    Set-NetFirewallRule -Name $rule -Enabled True -RemoteAddress $pi
}
Set-NetFirewallRule -Name 'RemoteDesktop-Shadow-In-TCP' -Enabled False

Write-Host ''
Write-Host 'Remote Desktop is ON (Network Level Authentication required).' -ForegroundColor Green
Get-NetFirewallRule -Group '@FirewallAPI.dll,-28752' | ForEach-Object {
    $from = ($_ | Get-NetFirewallAddressFilter).RemoteAddress -join ','
    '{0,-40} enabled={1,-5} allowed from={2}' -f $_.DisplayName, $_.Enabled, $from
}
Write-Host ''
Write-Host 'You can close this window.'
