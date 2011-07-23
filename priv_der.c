/* Private to DER key converter
 * Copyright (c) 2011 Matt Giuca
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

/* Link with -lssl. */

/* Usage: This program simply takes input on stdin, which must be a binary
 * file containing precisely 32 bytes, a private key.
 * Its output is also binary, 279 bytes containing a full DER key.
 * The output will contain both the private and public keys.
 * (The private key from bytes 9 - 40 inclusive; the public key from bytes 214
 * - 279 inclusive; the remaining bytes are always the same, containing
 * configuration information.)
 * You can use Python scripts to manipulate these bytes into human-workable
 * strings.
 */

#include <openssl/ecdsa.h>
#include <openssl/evp.h>
#include <openssl/bn.h>

#define PRIVATE_KEY_SIZE    32
#define PUBLIC_KEY_SIZE     65
#define DER_KEY_SIZE        279

/** Store a private key into an EC_KEY structure.
 * Note: This does not accept a full DER buffer. Just a (usually 32-byte)
 * private key.
 * This does not set the corresponding parameters or public key.
 * @param key An OpenSSL EC key, with valid private and public key components.
 * @param buf A buffer containing the private key.
 * @param len The length of buf.
 * @return 0 on success, 1 on error.
 */
int store_private_key(EC_KEY* key, const unsigned char* buf, int len)
{
    /* First, convert the buffer into a BIGNUM */
    BIGNUM* priv_key = BN_new();
    if (!priv_key)
    {
        fprintf(stderr, "BN_new failed\n");
        return 1;
    }
    BN_bin2bn(buf, len, priv_key);
    /* Then write the private key into the key structure (takes a copy of
     * priv_bn). */
    if (!EC_KEY_set_private_key(key, priv_key))
    {
        fprintf(stderr, "EC_KEY_set_private_key failed\n");
        BN_clear_free(priv_key);
        return 1;
    }
    BN_clear_free(priv_key);
    return 0;
}

/** Encode an EC_KEY into a DER public/private key structure.
 * Allocates a new buffer, and writes the key data in binary to the buffer.
 * Based on CKey::GetPrivKey in key.h in the Bitcoin distribution (SVN r146).
 * Copyright (c) 2009-2010 Satoshi Nakamoto.
 * @param key An OpenSSL EC key, with valid private and public key components.
 * @param len Will have the buffer length written.
 * @return An allocated buffer, or NULL on error.
 */
unsigned char* get_der_key(const EC_KEY* key, int* len)
{
    unsigned int nSize = i2d_ECPrivateKey((EC_KEY*) key, NULL);
    unsigned char* buffer;
    unsigned char* pbegin;
    if (!nSize)
    {
        fprintf(stderr, "i2d_ECPrivateKey failed\n");
        return NULL;
    }
    buffer = (unsigned char*) malloc(nSize);
    pbegin = buffer;
    if (i2d_ECPrivateKey((EC_KEY*) key, &pbegin) != nSize)
    {
        fprintf(stderr, "i2d_ECPrivateKey returned unexpected size\n");
        free(buffer);
        return NULL;
    }
    *len = nSize;
    return buffer;
}

/** Compute the public key for an EC_KEY with a private key.
 * The EC_KEY should have had a private key written to it. This will set its
 * public key to correspond to its private key.
 * @param key An OpenSSL EC key, with valid private and public key components.
 * @return 0 on success, 1 on error.
 */
int compute_public_key(EC_KEY* key)
{
    /* Based on EC_KEY_check_key in OpenSSL crypto/ec/ec_key.c.
     * (That code computes the public key, then checks if it equals the one in
     * the EC_KEY -- this code stores the computed public key in the EC_KEY.)
     * Comments based on very hazy knowledge from the Wikipedia article
     * "Elliptic Curve DSA".
     */
    /* The "group" is some part of the key configuration */
    const EC_GROUP* group = EC_KEY_get0_group(key);
    /* Get the private key as a BIGNUM */
    const BIGNUM* priv_key = EC_KEY_get0_private_key(key);
    /* The BTN_CTX is used for bignum calculations */
    BN_CTX* ctx = NULL;
    EC_POINT* point = NULL;
    ctx = BN_CTX_new();
    if (!ctx)
    {
        fprintf(stderr, "BN_CTX_new failed\n");
        goto err;
    }
    /* Initialise point to G, the base point of prime order on the curve. */
    point = EC_POINT_new(group);
    if (!point)
    {
        fprintf(stderr, "EC_POINT_new failed\n");
        goto err;
    }
    /* Multiply the private key by G, storing the result in point. */
    if (!EC_POINT_mul(group, point, priv_key, NULL, NULL, ctx))
    {
        fprintf(stderr, "EC_POINT_mul failed\n");
        goto err;
    }
    /* point is now the public key -- store it in key */
    if (!EC_KEY_set_public_key(key, point))
    {
        fprintf(stderr, "EC_KEY_set_public_key failed\n");
        goto err;
    }
    EC_POINT_free(point);
    BN_CTX_free(ctx);
    return 0;
err:
    EC_POINT_free(point);
    BN_CTX_free(ctx);
    return 1;
}

int main()
{
    EC_KEY* key;
    unsigned char priv_buf[PRIVATE_KEY_SIZE];
    unsigned char* buf;
    int len;

    /* Create a new EC_KEY object (initialised with curve parameters, but not
     * with a private/public key) */
    key = EC_KEY_new_by_curve_name(NID_secp256k1);
    if (key == NULL)
    {
        fprintf(stderr, "EC_KEY_new_by_curve_name failed\n");
        return 1;
    }

    /* Read the 32-byte private key from stdin, and store it into key */
    fread(priv_buf, 1, PRIVATE_KEY_SIZE, stdin);
    if (feof(stdin))
    {
        fprintf(stderr, "Requires %d bytes of input\n", PRIVATE_KEY_SIZE);
        return 1;
    }
    if (store_private_key(key, priv_buf, sizeof(priv_buf)))
        return 1;

    /* Compute the corresponding public key from the private key */
    if (compute_public_key(key))
        return 1;

    /* Make sure the key is good (public matches private, etc) */
    if (!EC_KEY_check_key(key))
    {
        fprintf(stderr, "EC_KEY_check_key failed\n");
        return 1;
    }

    /* Write the full DER key to stdout */
    buf = get_der_key(key, &len);
    if (!buf)
        return 1;
    fwrite(buf, 1, len, stdout);
    free(buf);

    /* Destroy the EC_KEY object */
    EC_KEY_free(key);
    return 0;
}
