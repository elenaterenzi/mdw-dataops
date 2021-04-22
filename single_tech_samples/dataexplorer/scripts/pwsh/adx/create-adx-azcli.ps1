<#
[Azure Data Explorer Create Cluster]
Azure Data Explorer resource provisioning
1. Azure Data Explorer Create Cluster
#>

#Reference Utility Function Scripts
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




$rsgExists = az group exists -n $rsgName
if ($rsgExists -eq 'false') {
    az group create -l $regionName -n $rsgName --location $LOCATION
}

az extension add -n kusto

az kusto cluster create --cluster-name azureclitest --sku name="Standard_D11_v2" tier="Standard" --resource-group testrg --location westus

az kusto database create --cluster-name azureclitest --database-name clidatabase --resource-group testrg --read-write-database soft-delete-period=P365D hot-cache-period=P31D location=westus

az kusto database show --database-name clidatabase --resource-group testrg --cluster-name azureclitest


New-AzKustoCluster -Name DataOpsHerman01 -ResourceGroupName HDataOps01  -Location 'southeastasia' -SkuName 'Standard_D11_v2' -SkuTier 'Standard' -SkuCapacity 2

# Register-AzureRmResourceProvider -ProviderNamespace Microsoft.Kusto'

New-AzKustoDatabase -Name dataopsdb -ClusterName DataOpsHerman01  -ResourceGroupName HDataOps01 -Kind ReadWrite  -Location 'southeastasia'


Write-Log "INFO" "Install requirements for adx database creation" 
#Install Required Packages
pip install -r (Join-Path -Path $dbProvisionToolPath -ChildPath "requirements.txt") --user


#Create ADX Tables
Write-Log "INFO" "Start to create $($config.ADX.DatabaseNum) tables"
python (Join-Path -Path $dbProvisionToolPath -ChildPath "create_dataexplorer_database.py") createTableofDatabase -s (Join-Path -Path $dbProvisionToolPath -ChildPath "FieldList") -c $config.ADX.DatabaseNum

#Remove Environment Variables
Set-Environment-Variables $config "delete"

