# DataOPs with Azure Data Explorer

This sample demonstrates the CI/CD process to create a multi-tenant Azure Data Explorer cluster.


[Azure Data Explorer](https://azure.microsoft.com/en-us/services/data-explorer/#features) is a fast, fully managed data analytics service for large volumes of data ingesting from applications, websites, IoT devices, and more. 

The following sample demonstrates how you can create CI/CD pipelines to provide Azure Data Explorer services and deploy database changes.  

## Contents

Contents of this sample includes: 

1. Provision Azure Data Explorer 
2. Create Multi-Tenanet Database and Table 
3. Validate Table/Database creation 


## Solution Overview

The solution will demonstrate how to use the CI/CD process to create a multi-tenant Azure Data Explorer cluster. We use [Multi-tenant app with database-per-tenant](https://docs.microsoft.com/en-us/azure/azure-sql/database/saas-tenancy-app-design-patterns#d-multi-tenant-app-with-database-per-tenant) design.   It will create multiple databases on a scalable ADX cluster to provide a cost-effective way of sharing resources across many databases. 

![imge](https://docs.microsoft.com/en-us/azure/azure-sql/database/media/saas-tenancy-app-design-patterns/saas-multi-tenant-app-database-per-tenant-pool-15.png)

Each database will share the same table schema. It also includes a system configuration file and a key vault for secrets. Table schema of the databases is defined in [Kusto query language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/concepts/#:~:text=Kusto%20query%20language%20is%20primary%20means%20of%20interaction.,queries%20and%20control%20commands%20are%20short%20textual%20%22programs%22.). 

In the CI/CD process, we will insert sample data into the provisioned tables and validate the result to test and validate the deployment. 

We will also create Azure Dashboard to monitor the critical metrics of the Azure Data Explorer cluster. 


### Architecture 

The following shows the architecture of the Azure Data Explorer multi-tenancy deploy and configure architecture. 

![img](./docs/images/architecture.png)

### Continuous Integration and Continuous Delivery
The following shows CI/CD flow suggested on the ADX DataOp pipeline.  
![img](./docs/images/adx_dev_op_flow.png)


### Technologies used
- [Azure Data Explorer](https://azure.microsoft.com/en-us/services/data-explorer/)
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/) 
- [Azure DevOps](https://docs.microsoft.com/en-us/azure/devops/?view=azure-devops)
- [Python 3.6+](https://www.python.org/downloads/release/python-360/)
- [Powershell Core (run on Ubuntu)](https://github.com/PowerShell/PowerShell)

## Key Learning 

The following summarizes key learnings and best practices demonstrated by this sample solution.

__1. Use a centralized configuration file to store ADX cluster provision parameters__

Azure Data Explorer is a powerful data analytics platform. To optimize systerm performance under different workloads, a lot of parameters can be set and choose. We put these parameters in central configuration files to simplify the configuration and management effort. 

__2. Include multi-tenancy resource creation as part of IaC (Infrastructure as Code).__

We saw many companies leverage Azure Data Explorer to build robust data analytical application to serve their customers. In the sample, we will demonstrate how to include multi-tenancy resource creation as part of IaC. With that implementation, it not only helps simply the validation multi-tenant implementation but also helps companies to easily track multi-tenancy implementation change.  


__3. Use sample data to test the resource provision result.__  

After provisioning the cluster, database and tables, we want to validate and test if we have a ready data repository for applications. We use sample data that mimic actual data to do the end-to-end ingestion and query testing to make sure the provisioned tables meet the requirements and are ready for use. 

__4. Store secrets in Azure Key Vault__
We store all secrets in Azure Key Vault to make sure this sensitive information is securely stored and protected. 

## Key Concepts

__1. Azure Data Explorer Configuration settings__

Azure Data Explorer has several components inside it, and each component could be configured with specific parameters to optimize its performance. To simplify the configuration, we put the most common configuration in a centralized JSON document to quickly understand all the settings. The deployment script will provision an ADX cluster based on the JSON.     

__2.  multi-tenancy setting and ADX Python Utility__  

To provide better flexibilities to support multi-tenancy deployment, we build an ADXUtiltiy library based on Kusto python SDk. The utility library can read multi-tenancy settings and deploy the corresponding database and tables. 
The multi-tenancy setting is in `./pipelines/ADX-Deployment.yml` files. 

ADX utility library also supports data insert and data query. We use it to insert sample data into tables to validate if we have the right configuration for multi-tenancy data. 

__3. Provision Pipeline__

We use ADO pipeline to provision the ADX cluster resources and connect each action together. Azure ADO pipeline helps to define the CI/CD process. 


- Following is the ADX pipeline in the sample
![img](./docs/images/adx_pipeline.png)


## How to use the sample 

### Prerequests 
- [Azure  Account](https://azure.microsoft.com/en-us/free) 
- [Azure DevOps Account](https://azure.microsoft.com/en-us/services/devops/?nav=min)
- [GitHub account](https://github.com/)

### Software Prequests
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) 
- [Powershell Core 7.x](https://docs.microsoft.com/en-us/powershell/scripting/whats-new/what-s-new-in-powershell-70?view=powershell-7.1)
- [Python 3.6+](https://www.python.org/downloads/release/python-360/)
- [Kusto Python SDK](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/api/python/kusto-python-client-library) 


### Setup and Deployment

To setup the samples, run the following:


1. **Initial Setup**
   1. Ensure that:
      - You are logged in to the Azure CLI. To login, run `az login`.
      - Azure CLI is targeting the Azure Subscription you want to deploy the resources to.
         - To set target Azure Subscription, run `az account set -s <AZURE_SUBSCRIPTION_ID>`
      - Azure CLI is targeting the Azure DevOps organization and project you want to deploy the pipelines to.
         - To set target Azure DevOps project, run `az devops configure --defaults organization=https://dev.azure.com/<MY_ORG>/ project=<MY_PROJECT>`
   2. **Import** this repository into a new Github repo. See [here](https://help.github.com/en/github/importing-your-projects-to-github/importing-a-repository-with-github-importer) on how to import a github repo. Importing is necessary for setting up git integration with Azure Data Factory.
   3. Set the following **required** environment variables:
       - **GITHUB_REPO** - Name of your imported github repo in this form `<my_github_handle>/<repo>`
       - **GITHUB_PAT_TOKEN** - a Github PAT token. Generate them [here](https://github.com/settings/tokens). This requires "repo" scope.

       Optionally, set the following environment variables:
       - **RESOURCE_GROUP_LOCATION** - Azure location to deploy resources. *Default*: `southeastasia`.
       - **AZURE_SUBSCRIPTION_ID** - Azure subscription id to use to deploy resources. *Default*: default azure subscription. To see your default, run `az account list`.
       - **DEPLOYMENT_ID** - string appended to all resource names. This is to ensure uniqueness of azure resource names. *Default*: random five character string.
       - **AZDO_PIPELINES_BRANCH_NAME** - git branch where Azure DevOps pipelines definitions are retrieved from. *Default*: master.

      To further customize the solution, set parameters in `arm.parameters` files located in the `infrastructure` folder.

2. **Deploy Azure resources**
   1. Clone locally the imported Github Repo, then `cd` into the `single_tech_samples/datafactory` folder of the repo
   2. Run `./scripts/pwsh/deploy-pipeline.ps1`.
      - After a successful deployment, you will find `./scripts/pwsh/config/provision-config.json` files containing essential configuration information per environment. 
   3. As part of the deployment script, this updated the Azure DevOps Release Pipeline YAML definition to point to your Github repository. **Commit and push up these changes.**




### Run the sample

1. **Create Service Principle for deploying resources**

    Run `./scripts/pwsh/create-service-principle.ps1`
     to setup the Service Principle for the deployment. 

2. **Modify the configuration files**

   1. Modify `./scripts/pwsh/config/provision-config.json` with the ADX cluster setting and resource name in your environment.
   2. Modify `./src/python/FieldList` which defines the table schema
   3. Modify `./pipelines/ADX-Deployment.yml` to change the database list, tables list and testing data files list for the system. 
   2. check-in the modified provision-config.json files 

3. **Run the pipeline to deploy the resources**

   Run the pipeline in Azure DevOp portal. 


![img](./docs/images/pipeline-create-multitenant.png)

Validate all test are successful 

![img](./docs/images/pipeline-test-tabes.png)

4. Check the Azure Monotor to see the whole system run. 

![img](./docs/images/pipeline-monitor.png)

### Known Issues, Limitation and Workarounds
1. 