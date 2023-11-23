@integration_test
 @ABGN-7575-Tag-Storage-Resources
 @Backups
 Feature: Tag Storage Resources

Scenario: Positive Scenario - Success
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the request body contains valid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 200 is returned
 And all the storage resources in the account tagged with the tag list in the request

Scenario: Negative Scenario - FailureWhenAuthTokenInvalid
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is invalid
 And the account is valid
 And the region is valid
 And the request body contains valid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 401 is returned

Scenario: Negative Scenario - FailureWhenRegionInvalid
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is valid
 And the account is valid
 And the region is invalid
 And the request body contains valid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 400 is returned

Scenario: Negative Scenario - FailureWhenAccountInvalid
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is valid
 And the account is invalid
 And the region is valid
 And the request body contains valid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 404 is returned

Scenario: Negative Scenario - FailureWhenResourceTypeInvalid
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the resourceType in url is invalid
 And the request body contains valid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 400 is returned

Scenario: Negative Scenario - FailureWhenTagListInvalid
 Given the api /v1/accounts/<account>/regions/<region>/resourceType/storage/tags exists
 And the auth token is valid
 And the account is valid
 And the region is valid
 And the request body contains invalid tags list
 And the account has at least one resource for each storage resource type
 When we invoke the api
 Then response code of 400 is returned