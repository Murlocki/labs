package main

import (
    "fmt"
    "log"
    "math/rand"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "text/plain; charset=utf-8")
        fmt.Fprintf(w, "\u041f\u0440\u0438\u0432\u0435\u0442 %d\n", 100+rand.Intn(900))
    })
    log.Fatal(http.ListenAndServe(":8090", nil))
}
