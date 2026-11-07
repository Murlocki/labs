FROM golang:alpine AS build
WORKDIR /src
COPY main.go .
RUN CGO_ENABLED=0 go build -o /go-check main.go

FROM scratch
COPY --from=build /go-check /go-check
EXPOSE 8090
ENTRYPOINT ["/go-check"]
