LDFLAGS = -lssl

priv_der: priv_der.c
	$(CC) -o $@ $(CFLAGS) $(LDFLAGS) $^
