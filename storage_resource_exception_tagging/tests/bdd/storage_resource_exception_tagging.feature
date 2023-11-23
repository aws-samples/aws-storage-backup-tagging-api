@integration_test
@ABGN-8749-Tag-Storage-Resources-Exception
@Backups
Feature: Tag Storage Resources Exception

Scenario: Positive Scenario - Success Enable
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/enable exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the request body contains valid resource list
 When we invoke the api
 Then response code of 200 is returned
 And all the storage resources in the request body are tagged with the tag key `vpcx-skip-backup` and tag value `true`
 And the message is 'storage resources tagged with tag key vpcx-skip-backup and tag value true'

Scenario: Positive Scenario - Success Disable
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/disable exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the request body contains valid resource list
 When we invoke the api
 Then response code of 200 is returned
 And all the storage resources in the request body are un tagged with the tag key `vpcx-skip-backup`
 And the message is 'storage resources un tagged with tag key vpcx-skip-backup'

Scenario: Negative Scenario - FailureWhenAuthTokenInvalid
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/<enable/disable> exists
 And the auth token is invalid
 And the account is valid
 And the region is valid
 And the request body contains valid resource list
 When we invoke the api
 Then response code of 401 is returned
 And the error message is 'unauthorized'

Scenario: Negative Scenario - FailureWhenRegionInvalid
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/<enable/disable> exists
 And the auth token is valid
 And the account is valid
 And the region is invalid
 And the request body contains valid resource list
 When we invoke the api
 Then response code of 400 is returned
 And the error message is 'region not found'

Scenario: Negative Scenario - FailureWhenAccountInvalid
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/<enable/disable> exists
 And the auth token is valid
 And the account is invalid
 And the region is valid
 And the request body contains valid resource list
 When we invoke the api
 Then response code of 404 is returned
 And the error message is 'account not found'

Scenario: Negative Scenario - FailureWhenResourceInvalid
 Given the api /v1/accounts/<account>/regions/<region>/exceptions/backup/<enable/disable> exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the request body contains invalid resource list
 When we invoke the api
 Then response code of 400 is returned
 And error message is 'One of the resources in the request is invalid.'