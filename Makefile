export PYROP:="$(CURDIR)/pyrop"

ROPDB_FILE = ropdb/$(VERSION).py

all: check_ropdb rop/build

check_ropdb:
ifndef VERSION
	$(error Usage: make VERSION=<app_version>)
endif
ifeq ($(wildcard $(ROPDB_FILE)),)
	$(error RopDB file $(ROPDB_FILE) not found!)
endif

rop/build: make_kernelhaxcode ropdb/$(VERSION).py
	@cp ropdb/$(VERSION).py ropdb/ropdb.py
	@make -C rop all

make_kernelhaxcode :
	@make -C kernelhaxcode_3ds-full all

clean:
	@make -C kernelhaxcode_3ds-full clean
	@make -C rop clean
	@rm -f ropdb/ropdb.py
