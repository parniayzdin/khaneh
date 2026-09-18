package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
	"unicode/utf8"
)

// Only configured routes reach the local Python service; clients cannot choose a URL.
func registerAI(mux *http.ServeMux) {
	base := os.Getenv("KHANEH_AI_URL")
	if base == "" {
		base = "http://127.0.0.1:8001"
	}
	client := &http.Client{Timeout: 25 * time.Second, CheckRedirect: func(r *http.Request, via []*http.Request) error { return http.ErrUseLastResponse }}
	for route, upstream := range map[string]string{"/api/ask": "/ask", "/api/search": "/search", "/api/ai/health": "/health"} {
		mux.HandleFunc("GET "+route, aiHandler(client, strings.TrimRight(base, "/")+upstream, upstream))
	}
}

func aiHandler(client *http.Client, target, endpoint string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		params := url.Values{}
		if endpoint != "/health" {
			q := strings.TrimSpace(r.URL.Query().Get("q"))
			if n := utf8.RuneCountInString(q); n < 2 || n > 300 {
				writeJSON(w, 400, map[string]string{"error": "Please enter a question between 2 and 300 characters."})
				return
			}
			params.Set("q", q)
			if endpoint == "/ask" {
				params.Set("person_id", r.URL.Query().Get("person_id"))
			}
			if endpoint == "/search" && r.URL.Query().Has("limit") {
				params.Set("limit", r.URL.Query().Get("limit"))
			}
		}
		req, err := http.NewRequestWithContext(r.Context(), "GET", target+"?"+params.Encode(), nil)
		if err != nil {
			writeJSON(w, 503, map[string]string{"error": "AI service is not configured correctly."})
			return
		}
		response, err := client.Do(req)
		if err != nil {
			writeJSON(w, 503, map[string]string{"error": "AI answers are unavailable. Start the Python service on port 8001 and try again."})
			return
		}
		defer response.Body.Close()
		data, err := io.ReadAll(io.LimitReader(response.Body, 1024*1024+1))
		if err != nil || len(data) > 1024*1024 || !json.Valid(data) {
			writeJSON(w, 502, map[string]string{"error": "The AI service returned an invalid response."})
			return
		}
		if response.StatusCode >= 500 {
			writeJSON(w, 503, map[string]string{"error": "AI answers are temporarily unavailable. Please try again."})
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.WriteHeader(response.StatusCode)
		w.Write(data)
	}
}
