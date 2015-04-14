#! /bin/zsh

dir=${1:-"."}
#echo "******* Checking Exceptions"
foreach d (./${dir}/**/*.log)
do
echo "Report on Exceptions for $d"
grep -A 15 -e "----- Begin Fatal Exception" "$d"
done

### %MSG-e TooManyClusters:   PhotonConversionTrajectorySeedProducerFromSingleLeg:photonConvTrajSeedFromSingleLeg  27-May-2014 14:48:03 CEST Run: 1 Event: 7
#echo "******* Checking Severity ERROR"
foreach d (./${dir}/**/*.log)
do
echo "Report on ERRORS for $d"
grep -e "\%MSG-e" "$d" | \
gawk '{print $1 $2 $3}' | \
perl -ne 'BEGIN{%sys=()} if(m#(.*)%MSG-[e](.*)#) {push @{$sys{$1}{$2}},1;} END{foreach $file (keys %sys) {foreach $sub (keys %{$sys{$file}}) {print "$file\t$sub\t". scalar @{$sys{$file}{$sub}}."\n" }}}' | \
sort -n
done

#echo "******* Checking Severity WARNING"
foreach d (./${dir}/**/*.log)
do
echo  "Report on WARNINGS for $d"
grep -e "\%MSG-w" "$d" | \
gawk '{print $1 $2 $3}' | \
perl -ne 'BEGIN{%sys=()} if(m#(.*)%MSG-[w](.*)#) {push @{$sys{$1}{$2}},1;} END{foreach $file (keys %sys) {foreach $sub (keys %{$sys{$file}}) {print "$file\t$sub\t". scalar @{$sys{$file}{$sub}}."\n" }}}' | \
sort -n 
done
