#!/usr/local/bin/perl
# Update the list of shared IP addresses

require './virtual-server-lib.pl';
&foreign_require("net", "net-lib.pl");
&error_setup($text{'sharedips_err'});
&can_edit_templates() || &error($text{'sharedips_ecannot'});
&ReadParse();

# Validate inputs, and check for clashes
@ips = split(/\s+/, $in{'ips'});
if (defined(&list_resellers)) {
	@rips = map { $_->{'acl'}->{'defip'} }
		    grep { $_->{'acl'}->{'defip'} } &list_resellers();
	}
@active = map { $_->{'address'} } &net::active_interfaces();
foreach $ip (@ips) {
	&check_ipaddress($ip) || &error(&text('sharedips_eip', $ip));
	$ip ne &get_default_ip() || &error(&text('sharedips_edef', $ip));
	&indexof($ip, @rips) < 0 || &error(&text('sharedips_erip', $ip));
	$d = &get_domain_by("ip", $ip, "virt", 1);
	$d && error(&text('sharedips_edom', $ip, $d->{'dom'}));
	&indexof($ip, @active) >= 0 || &error(&text('sharedips_eactive', $ip));
	}

# Check if one taken away was in use
@oldips = &list_shared_ips();
foreach $ip (@oldips) {
	if (&indexof($ip, @ips) < 0) {
		$d = &get_domain_by("ip", $ip);
		$d && &error(&text('sharedips_eaway', $ip, $d->{'dom'}));
		}
	}

# Save them
&lock_file($module_config_file);
&save_shared_ips(@ips);
&unlock_file($module_config_file);

&webmin_log("sharedips");
&redirect("");

