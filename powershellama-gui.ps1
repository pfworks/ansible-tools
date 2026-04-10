<#
.SYNOPSIS
    PowerSheLLama GUI - Windows GUI wrapper around powershellama with model/service selection.
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$SHELLAMA_API = if ($env:SHELLAMA_API) { $env:SHELLAMA_API } elseif ($env:ANSIBLE_TOOLS_API) { $env:ANSIBLE_TOOLS_API } else { "http://192.168.1.229:5000" }
$SHELLAMA_MODEL = if ($env:SHELLAMA_MODEL) { $env:SHELLAMA_MODEL } else { "qwen2.5-coder:7b" }

# --- Main Form ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "SheLLama"
$form.Size = New-Object System.Drawing.Size(1000, 700)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$font = New-Object System.Drawing.Font("Consolas", 10)
$form.Font = $font

# --- Top Panel ---
$topPanel = New-Object System.Windows.Forms.FlowLayoutPanel
$topPanel.Dock = "Top"
$topPanel.Height = 40
$topPanel.BackColor = $form.BackColor
$topPanel.Padding = New-Object System.Windows.Forms.Padding(5)

$lblApi = New-Object System.Windows.Forms.Label
$lblApi.Text = "API:"
$lblApi.AutoSize = $true
$topPanel.Controls.Add($lblApi)

$txtApi = New-Object System.Windows.Forms.TextBox
$txtApi.Text = $SHELLAMA_API
$txtApi.Width = 250
$txtApi.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 45)
$txtApi.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$topPanel.Controls.Add($txtApi)

$lblModel = New-Object System.Windows.Forms.Label
$lblModel.Text = "  Model:"
$lblModel.AutoSize = $true
$topPanel.Controls.Add($lblModel)

$cmbModel = New-Object System.Windows.Forms.ComboBox
$cmbModel.Width = 200
$cmbModel.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 45)
$cmbModel.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$cmbModel.DropDownStyle = "DropDownList"
$cmbModel.Items.Add($SHELLAMA_MODEL)
$cmbModel.SelectedIndex = 0
$topPanel.Controls.Add($cmbModel)

$btnRefresh = New-Object System.Windows.Forms.Button
$btnRefresh.Text = "↻ Models"
$btnRefresh.Width = 80
$btnRefresh.FlatStyle = "Flat"
$btnRefresh.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 45)
$btnRefresh.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$topPanel.Controls.Add($btnRefresh)

$form.Controls.Add($topPanel)

# --- Terminal Output ---
$txtOutput = New-Object System.Windows.Forms.RichTextBox
$txtOutput.Dock = "Fill"
$txtOutput.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$txtOutput.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$txtOutput.Font = $font
$txtOutput.ReadOnly = $true
$txtOutput.BorderStyle = "None"
$form.Controls.Add($txtOutput)

# --- Input Panel ---
$inputPanel = New-Object System.Windows.Forms.Panel
$inputPanel.Dock = "Bottom"
$inputPanel.Height = 35
$inputPanel.BackColor = $form.BackColor

$lblPrompt = New-Object System.Windows.Forms.Label
$lblPrompt.Text = "🔴 PS>"
$lblPrompt.AutoSize = $true
$lblPrompt.Location = New-Object System.Drawing.Point(5, 8)
$inputPanel.Controls.Add($lblPrompt)

$txtInput = New-Object System.Windows.Forms.TextBox
$txtInput.Location = New-Object System.Drawing.Point(65, 5)
$txtInput.Width = $form.ClientSize.Width - 75
$txtInput.Anchor = "Left,Right,Top"
$txtInput.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 45)
$txtInput.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 0)
$txtInput.Font = $font
$inputPanel.Controls.Add($txtInput)

$form.Controls.Add($inputPanel)

# Ensure terminal is above input but below top
$txtOutput.BringToFront()

# --- Functions ---
function Write-Terminal {
    param([string]$Text, [System.Drawing.Color]$Color = [System.Drawing.Color]::FromArgb(0, 255, 0))
    $txtOutput.SelectionStart = $txtOutput.TextLength
    $txtOutput.SelectionColor = $Color
    $txtOutput.AppendText("$Text`n")
    $txtOutput.ScrollToCaret()
}

function Invoke-ShellamaAPI {
    param([string]$Endpoint, [hashtable]$Body)
    $api = $txtApi.Text
    $json = $Body | ConvertTo-Json -Depth 10
    $resp = Invoke-RestMethod -Uri "$api$Endpoint" -Method Post -Body $json -ContentType "application/json" -TimeoutSec 600
    return $resp
}

function Refresh-Models {
    $cmbModel.Items.Clear()
    try {
        $resp = Invoke-RestMethod -Uri "$($txtApi.Text)/models" -TimeoutSec 10
        foreach ($m in $resp.models) {
            $sizeGb = [math]::Round($m.size / 1GB, 1)
            $cmbModel.Items.Add($m.name)
        }
        if ($cmbModel.Items.Count -gt 0) { $cmbModel.SelectedIndex = 0 }
        Write-Terminal "Loaded $($cmbModel.Items.Count) models" ([System.Drawing.Color]::Gray)
    } catch {
        $cmbModel.Items.Add($SHELLAMA_MODEL)
        $cmbModel.SelectedIndex = 0
        Write-Terminal "Could not fetch models: $_" ([System.Drawing.Color]::Red)
    }
}

function Process-Input {
    $line = $txtInput.Text.Trim()
    $txtInput.Clear()
    if (-not $line) { return }

    $model = $cmbModel.SelectedItem
    Write-Terminal "🔴 PS> $line" ([System.Drawing.Color]::White)

    if ($line -in @('exit', 'quit')) { $form.Close(); return }

    if ($line.StartsWith(",")) {
        $query = $line.Substring(1).Trim()
        if ($query -eq 'list' -or $query -eq 'help') {
            Write-Terminal ",  <prompt>       agentic chat" ([System.Drawing.Color]::Yellow)
            Write-Terminal ",explain  <file>  explain any file" ([System.Drawing.Color]::Yellow)
            Write-Terminal ",generate <desc>  generate code" ([System.Drawing.Color]::Yellow)
            Write-Terminal ",analyze  <path>  analyze files/dirs" ([System.Drawing.Color]::Yellow)
            Write-Terminal ",img <prompt>     generate image" ([System.Drawing.Color]::Yellow)
            Write-Terminal ",models           select model" ([System.Drawing.Color]::Yellow)
            return
        }
        if ($query -eq 'models') { Refresh-Models; return }

        # Route to appropriate endpoint
        try {
            if ($query.StartsWith('explain ')) {
                $file = $query.Substring(8).Trim()
                $content = Get-Content $file -Raw -ErrorAction Stop
                $ext = [IO.Path]::GetExtension($file).ToLower()
                if ($ext -in @('.yml', '.yaml')) {
                    $resp = Invoke-ShellamaAPI "/explain" @{ playbook = $content; model = $model }
                    Write-Terminal $resp.explanation ([System.Drawing.Color]::Cyan)
                } else {
                    $resp = Invoke-ShellamaAPI "/explain-code" @{ code = $content; model = $model }
                    Write-Terminal $resp.explanation ([System.Drawing.Color]::Cyan)
                }
            }
            elseif ($query.StartsWith('generate ')) {
                $desc = $query.Substring(9).Trim()
                if ($desc -match 'ansible|playbook') {
                    $resp = Invoke-ShellamaAPI "/generate" @{ commands = $desc; model = $model }
                    Write-Terminal $resp.playbook ([System.Drawing.Color]::Cyan)
                } else {
                    $resp = Invoke-ShellamaAPI "/generate-code" @{ description = $desc; model = $model }
                    Write-Terminal $resp.code ([System.Drawing.Color]::Cyan)
                }
            }
            elseif ($query.StartsWith('img ')) {
                $imageModel = if ($env:AI_IMAGE_MODEL) { $env:AI_IMAGE_MODEL } else { "sd-turbo" }
                $steps = if ($imageModel -match "turbo") { 4 } else { 20 }
                $resp = Invoke-ShellamaAPI "/generate-image" @{ prompt = $query.Substring(4).Trim(); image_model = $imageModel; steps = $steps; width = 512; height = 512 }
                if ($resp.image) {
                    $outfile = "$PWD\generated_$([int](Get-Date -UFormat %s)).png"
                    [IO.File]::WriteAllBytes($outfile, [Convert]::FromBase64String($resp.image))
                    Write-Terminal "Saved: $outfile" ([System.Drawing.Color]::Cyan)
                }
            }
            else {
                # Default: chat
                $resp = Invoke-ShellamaAPI "/chat" @{ message = $query; model = $model }
                if ($resp.error) { Write-Terminal "Error: $($resp.error)" ([System.Drawing.Color]::Red) }
                else { Write-Terminal $resp.response ([System.Drawing.Color]::Cyan) }
            }
            if ($resp.elapsed) {
                Write-Terminal "[$($resp.elapsed)s | $($resp.total_tokens) tokens | $model]" ([System.Drawing.Color]::Gray)
            }
        } catch {
            Write-Terminal "Error: $_" ([System.Drawing.Color]::Red)
        }
    }
    else {
        # Regular PowerShell command
        try {
            $output = Invoke-Expression $line 2>&1 | Out-String
            if ($output.Trim()) { Write-Terminal $output.Trim() }
        } catch {
            Write-Terminal $_.Exception.Message ([System.Drawing.Color]::Red)
        }
    }
}

# --- Events ---
$btnRefresh.Add_Click({ Refresh-Models })

$txtInput.Add_KeyDown({
    if ($_.KeyCode -eq 'Return') {
        $_.SuppressKeyPress = $true
        Process-Input
    }
})

# --- Startup ---
Write-Terminal "SheLLama - PowerShell + AI agent" ([System.Drawing.Color]::Cyan)
Write-Terminal "Type , for AI commands, ,list for help" ([System.Drawing.Color]::Gray)
Write-Terminal ""
Refresh-Models
$txtInput.Focus()

[void]$form.ShowDialog()
