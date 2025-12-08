emtester 24g
memtester 24g 1

sudo memtester 24g 1

sudo lshw -C memory

sudo stressapptest -M 24000 -s 300

lshw -C memory | grep -i configured

sudo dmidecode --type 17 | grep -i speed

sysbench memory run --memory-block-size=1G --memory-total-size=50G

mbw -n 100 1G

perf stat -d dd if=/dev/zero of=/dev/null bs=1M count=20000

perf stat mbw 1G

mbw -n 100 1G

mbw -n 10 10G
mbw -n 1 100G

mbw -n 100 1G
mbw -n 1000 1G

