![pylint](https://github.com/dfar-io/app-gateway-cert-checker/actions/workflows/pylint.yml/badge.svg)
[![Maintainability](https://api.codeclimate.com/v1/badges/984972906be25b9f2bfc/maintainability)](https://codeclimate.com/github/dfar-io/app-gateway-cert-checker/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/984972906be25b9f2bfc/test_coverage)](https://codeclimate.com/github/dfar-io/app-gateway-cert-checker/test_coverage)

# app-gateway-cert-checker

Automatically checks certs for all Azure Application Gateways.

## Getting started

To get started, create an `.env` file copied from `.env.example`.

If needed, you can generate an Azure service principal with the following command:

```
az login
az ad sp create-for-rbac --name ServicePrincipalName --skip-assignment true
```

You can use the values provided in your `.env` file, and then assign the service principal
to all appropriate Application Gateways.

## Reference

[Azure CLI Service Principal creation](https://docs.microsoft.com/en-us/cli/azure/ad/sp?view=azure-cli-latest#az_ad_sp_create_for_rbac)
