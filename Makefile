export PYROP:="$(CURDIR)/pyrop"

ROPDB_FILE = db/$(VERSION).py

all: check_ropdb rop/build

check_ropdb:
ifndef VERSION
	$(error Usage: make VERSION=<app_version>)
endif
ifeq ($(wildcard $(ROPDB_FILE)),)
	$(error RopDB file $(ROPDB_FILE) not found!)
endif

rop/build: make_kernelhaxcode db/$(VERSION).py
	@cp db/$(VERSION).py db/ropdb.py
	@make -C rop all

make_kernelhaxcode :
	@make -C kernelhaxcode_3ds-full all

clean:
	@make -C kernelhaxcode_3ds-full clean
	@make -C rop clean
	@rm -f db/ropdb.py
