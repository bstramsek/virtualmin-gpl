#!/usr/local/bin/perl
# Create, update or delete a record

require './virtual-server-lib.pl';
&ReadParse();
&error_setup($text{'record_err'});
$d = &get_domain($in{'dom'});
$d || &error($text{'edit_egone'});
&can_edit_domain($d) || &error($text{'edit_ecannot'});
&require_bind();
($recs, $file) = &get_domain_dns_records_and_file($d);
$file || &error($recs);

if (!$in{'type'}) {
	# Get the record
	($r) = grep { $_->{'id'} eq $in{'id'} } @$recs;
	$r || &error($text{'record_egone'});
	}
else {
	# Creating a new one
	$r = { 'type' => $in{'type'},
	       'class' => 'IN' };
	}

&obtain_lock_dns($d);
if ($in{'delete'}) {
	# Just delete it
	&can_delete_record($d, $r) || &error($text{'record_edelete'});
	&bind8::delete_record($file, $r);
	}
else {
	# Validate and store inputs
	($t) = grep { $_->{'type'} eq $r->{'type'} } &list_dns_record_types($d);
	&can_edit_record($d, $r) && $t || &error($text{'record_eedit'});
	if ($in{'type'} || $r->{'name'} ne $d->{'dom'}.".") {
		# Validate name
		if ($in{'name_def'}) {
			$r->{'name'} = $d->{'dom'}.".";
			}
		else {
			$in{'name'} =~ /^[a-z0-9\.\_\-]+$/i ||
			    $in{'name'} eq '*' ||
				&error($text{'record_ename'});
			($in{'name'} =~ /^\./ || $in{'name'} =~ /\.$/) &&
				&error($text{'record_enamedot'});
			$r->{'name'} = $in{'name'}.".".$d->{'dom'}.".";
			}
		}

	# Validate TTL
	if ($in{'ttl_def'}) {
		delete($r->{'ttl'});
		}
	else {
		$in{'ttl'} =~ /^\d+$/ && $in{'ttl'} > 0 ||
			&error($text{'record_ettl'});
		$in{'ttl_units'} =~ /^[a-z]$/i ||
			&error($text{'record_ettlunits'});
		$r->{'ttl'} = $in{'ttl'}.$in{'ttl_units'};
		}

	# Validate values
	@vals = @{$t->{'values'}};
	$r->{'values'} = [ ];
	for(my $i=0; $i<@vals; $i++) {
		$v = $in{'value_'.$i};
		$re = $vals[$i]->{'regexp'};
		$fn = $vals[$i]->{'func'};
		!$re || $v =~ /$re/ ||
			&error(&text('record_evalue', $vals[$i]->{'desc'}));
		$err = $fn && &$fn($v);
		$err && &error($err);
		if ($vals[$i]->{'dot'} && $v =~ /\./ && $v !~ /\.$/) {
			# Append dot to value, in case user forgot it
			$v .= ".";
			}
		push(@{$r->{'values'}}, $v);
		}

	# Check for CNAME collision
	$newrecs = [ @$recs ];
	push(@$newrecs, $r) if ($in{'type'});
	if ($r->{'type'} eq 'CNAME') {
		%clash = map { $_->{'name'}, $_ }
			     grep { $_ ne $r } @$newrecs;
		foreach $e (@$newrecs) {
			if ($e->{'type'} eq 'CNAME' && $clash{$r->{'name'}}) {
				&error(&text('record_ecname', $r->{'name'}));
				}
			}
		}

	@params = ( $r->{'name'}, $r->{'ttl'}, $r->{'class'}, $r->{'type'},
		    &join_record_values($r), $r->{'comment'} );
	if ($in{'type'}) {
		# Create the record
		&bind8::create_record($file, @params);
		}
	else {
		# Just update it
		&bind8::modify_record($file, $r, @params);
		}
	}
&post_records_change($d, $recs, $file);
&release_lock_dns($d);
&reload_bind_records($d);
&webmin_log($in{'delete'} ? 'delete' : $in{'type'} ? 'create' : 'modify',
	    'record', $d->{'dom'}, $r);
&redirect("list_records.cgi?dom=$in{'dom'}");

