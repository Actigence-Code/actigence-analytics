# MinIO used by Analytics tests

`make minio` builds this local test image, starts the same S3/console ports and
creates the existing four buckets with their seven-day expiration rules. The
native MinIO test selection and assertions are unchanged. No image is published.

The former `minio/minio:latest` image is no longer anonymously available. The
MinIO community project documents source-only distribution, so this Dockerfile
builds the **official community sources**, rather than using a third-party S3
server or requiring registry credentials. This is a local Analytics CI build,
not an image published or supported by MinIO. It is not a production deployment.

The source archives are pinned by full commit and verified SHA-256. The Go
compiler and runtime base are pinned by OCI digest. Go uses the original
`go.mod`/`go.sum`, `-mod=readonly`, the module proxy/checksum database, and no
automatic compiler download. Module/build caches are shared between server and
client compilation, then removed from the build layer to limit CI disk usage.
Both upstream LICENSE, NOTICE and CREDITS files are retained in the runtime image.

| Component | Upstream revision |
|---|---|
| Server | `minio/minio@7aac2a2c5b7c882e68c1ce017d8256be2feea27f` |
| Client | `minio/mc@77f82e18b5401a65958f1619df6ebb994634bd88` |
| Compiler | Go `1.27.3-alpine`, digest in `Dockerfile` |
| Runtime | Alpine `3.24`, digest in `Dockerfile` |

Update sources or base images only with a corresponding checksum/digest update
and real qualification of bucket creation, lifecycle, object transfer and
signed S3 access. A successful image build alone does not qualify the Analytics
integration; the normal `mix test --include minio` jobs must still pass.

Official references:

- https://github.com/minio/minio#source-only-distribution
- https://github.com/minio/minio/tree/7aac2a2c5b7c882e68c1ce017d8256be2feea27f
- https://github.com/minio/mc/tree/77f82e18b5401a65958f1619df6ebb994634bd88
