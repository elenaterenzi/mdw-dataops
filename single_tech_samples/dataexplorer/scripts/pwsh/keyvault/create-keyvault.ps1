<#
[Azure Data Explorer Create Cluster]
Azure Data Explorer resource provisioning
1. Azure Data Explorer Create Cluster
#>

#Reference Utility Function Scripts
. "..\util\common-util.ps1"
. "..\util\azure-util.ps1"

Write-Log "INFO"  "==== ADX DevOp Project - Create KeyVault  ===="
Write-Log "INFO"  "====================================================================" 

#Get Global Config
$config = Get-Content ..\config\provision-config.json | ConvertFrom-Json

#Start to deploy Azure Resources
Write-Log "INFO" "Before deployment, please make sure you have installed the Powershell Core (version 6.x up) and latest Azure Cli"

Write-Log "INFO" "Connect to Azure using Service Principal" 
# Connect to Azure
Connect-Azure $config


az group create --name $config.ResourceGroupName -l $config.Location


Write-Log "INFO" "Start Create Azure Key Vault" 

az keyvault create  --name $config.KeyVault.KeyVaultName  --resource-group $config.ResourceGroupName

Write-Log "INFO" "Set Azure Key Vault Value" 

az keyvault secret set   --name "spid"   --vault-name $config.KeyVault.KeyVaultName  --value   $config.DeployClientId

az keyvault secret set   --name "spid-secret"   --vault-name  $config.KeyVault.KeyVaultName  --value  $config.DeploySecret

