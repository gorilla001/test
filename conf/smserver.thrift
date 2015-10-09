namespace py sqc

service Smserver {
    string ping(),
    oneway void sendsms(1:required string sender, 2:required list<string> to, 3:required string content)
}
