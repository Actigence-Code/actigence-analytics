# Community images are no longer public: build the official pinned sources.
FROM golang:1.27.3-alpine@sha256:b8c9b82affbbb82a020bbcf998dad2ba9516944ac7e883524642a481a9505e9c AS compiler
ENV CGO_ENABLED=0 GOTOOLCHAIN=local GOTELEMETRY=off GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
ADD --checksum=sha256:71794c2df26aad0cc99e8421c58b7aa2dd55969f979b0e7d1e931042e9fabcd6 https://codeload.github.com/minio/minio/tar.gz/7aac2a2c5b7c882e68c1ce017d8256be2feea27f /tmp/minio.tar.gz
ADD --checksum=sha256:167415edd21bc29f5360943dac64272aa5cda0a39f3070b15cfeca671c43d975 https://codeload.github.com/minio/mc/tar.gz/77f82e18b5401a65958f1619df6ebb994634bd88 /tmp/mc.tar.gz
# A single stage shares Go's module/cache trees. Drop them before committing its
# layer so CI does not retain two copies of these large transient dependencies.
RUN mkdir -p /source/server /source/client /out/licenses/minio /out/licenses/mc \
    && tar -xzf /tmp/minio.tar.gz -C /source/server --strip-components=1 \
    && tar -xzf /tmp/mc.tar.gz -C /source/client --strip-components=1 \
    && cd /source/server && go build -p 2 -mod=readonly -trimpath -buildvcs=false -o /out/minio . \
    && cd /source/client && go build -p 2 -mod=readonly -trimpath -buildvcs=false -o /out/mc . \
    && cp /source/server/LICENSE /source/server/NOTICE /source/server/CREDITS /out/licenses/minio/ \
    && cp /source/client/LICENSE /source/client/NOTICE /source/client/CREDITS /out/licenses/mc/ \
    && go clean -modcache -cache && rm -rf /source /tmp/minio.tar.gz /tmp/mc.tar.gz

FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
LABEL org.opencontainers.image.title="Analytics CI MinIO from official community source" \
      org.opencontainers.image.source="https://github.com/minio/minio" \
      org.opencontainers.image.revision="7aac2a2c5b7c882e68c1ce017d8256be2feea27f" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"
COPY --from=compiler /out/minio /usr/local/bin/minio
COPY --from=compiler /out/mc /usr/local/bin/mc
COPY --from=compiler /out/licenses /usr/share/licenses
COPY --from=compiler /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
ENTRYPOINT ["/usr/local/bin/minio"]
