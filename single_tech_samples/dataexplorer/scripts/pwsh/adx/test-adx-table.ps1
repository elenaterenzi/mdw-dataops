. "..\util\common-util.ps1"
. "..\util\azure-util.ps1"

Write-Log "INFO"  "==== ADX DevOp Project - Create ADX services, Databases, Tables ===="
Write-Log "INFO"  "====================================================================" 

#Get Global Config
$config = Get-Content ..\config\provision-config.json | ConvertFrom-Json


Function Set-Environment-Variables {
    [CmdletBinding()]
    Param(
    [Parameter(Mandatory=$True)]
    [Object]
    $configObj,
    [Parameter(Mandatory=$True)]
    [ValidateSet("create","delete")]
    [String]
    $action
    )
    if($action.ToLower().Equals("create")){
        $clusterName = $configObj.ADX.ClusterName
        [Environment]::SetEnvironmentVariable('RETENTION_DAYS',$configObj.ADX.TableRetentionDays)
        [Environment]::SetEnvironmentVariable('CLIENT_ID',$configObj.DeployClientId)
        [Environment]::SetEnvironmentVariable('CLIENT_SECRET',$configObj.DeploySecret)
        [Environment]::SetEnvironmentVariable('TENANT_ID',$configObj.AzureTenantId)
        [Environment]::SetEnvironmentVariable('REGION',$configObj.Location)
        [Environment]::SetEnvironmentVariable('CLUSTER_NAME',$clusterName)
        [Environment]::SetEnvironmentVariable('SUBSCRIPTION_ID',$configObj.AzureSubscriptionId)
        [Environment]::SetEnvironmentVariable('RESOURCE_GROUP',$configObj.ResourceGroupName)
    }
    elseif ($action.ToLower().Equals("delete")){
        [Environment]::SetEnvironmentVariable('RETENTION_DAYS',$null)
        [Environment]::SetEnvironmentVariable('CLIENT_ID',$null)
        [Environment]::SetEnvironmentVariable('CLIENT_SECRET',$null)
        [Environment]::SetEnvironmentVariable('TENANT_ID',$null)
        [Environment]::SetEnvironmentVariable('REGION',$null)
        [Environment]::SetEnvironmentVariable('CLUSTER_NAME',$null)
        [Environment]::SetEnvironmentVariable('SUBSCRIPTION_ID',$null)
        [Environment]::SetEnvironmentVariable('RESOURCE_GROUP',$null)
    }
}


#Start to deploy Azure Resources
Write-Log "INFO" "Before deployment, please make sure you have installed the Powershell Core (version 6.x up) and latest Azure Cli"

Write-Log "INFO" "Connect to Azure using Service Principal" 
# Connect to Azure
Connect-Azure $config


#Set up Environment Variables
Set-Environment-Variables $config "create"

$dbProvisionToolPath = "../../code/Tables/"

Write-Host "** Azure Subcription Name is $($config.AzureSubscriptionName)"
Write-Host "** Azure Subcription ID is $($config.AzureSubscriptionId)"
Write-Host "** Azure tenantId ID is $($config.AzureTenantId)"
Write-Host "** Azure User Name(Application/Client ID) is  $($config.AppName)"
Write-Host "** Azure Object ID is  $($config.DeployObjectId)"


$path = [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')
Write-Host "** Azure Subcription Name is $($path)"
$clientid = [Environment]::GetEnvironmentVariable('CLIENT_ID')
Write-Host "** Azure Client ID is $($clientid)"


Set-Environment-Variables $config "delete"