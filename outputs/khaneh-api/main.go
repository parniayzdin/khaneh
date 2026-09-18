package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"time"
)

type Person struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Persian string `json:"persian"`
	City    string `json:"city"`
	Year    int    `json:"year"`
	Date    string `json:"date"`
	Image   string `json:"image"`
	Tags    string `json:"tags,omitempty"`
	Story   string `json:"story"`
	Credit  string `json:"credit"`
	Sources []struct {
		Title string `json:"title"`
		URL   string `json:"url"`
	} `json:"sources"`
}

// Load once at startup; reject incomplete or duplicate records.
func loadPeople(path string) ([]Person, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var people []Person
	if err = json.Unmarshal(data, &people); err != nil {
		return nil, err
	}
	if len(people) == 0 {
		return nil, fmt.Errorf("no memorial records found")
	}
	seen := map[string]bool{}
	for _, p := range people {
		if p.ID == "" || p.Name == "" || p.City == "" || p.Image == "" || p.Story == "" || len(p.Sources) == 0 || seen[p.ID] {
			return nil, fmt.Errorf("incomplete or duplicate record: %q", p.ID)
		}
		seen[p.ID] = true
	}
	return people, nil
}
func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		log.Printf("Write response: %v", err)
	}
}
func newHandler(people []Person) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]any{"service": "Khaneh API", "endpoints": []string{"/health", "/api/people", "/api/people/{id}"}})
	})
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]any{"status": "ready", "service": "Khaneh API", "people": len(people), "storage": "json"})
	})
	mux.HandleFunc("GET /api/people", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, people) })
	mux.HandleFunc("GET /api/people/{id}", func(w http.ResponseWriter, r *http.Request) {
		for _, p := range people {
			if p.ID == r.PathValue("id") {
				writeJSON(w, 200, p)
				return
			}
		}
		writeJSON(w, 404, map[string]string{"error": "Person not found"})
	})
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		w.Header().Add("Vary", "Origin")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		if origin == "http://localhost:4173" || origin == "http://127.0.0.1:4173" {
			w.Header().Set("Access-Control-Allow-Origin", origin)
		}
		mux.ServeHTTP(w, r)
	})
}
func main() {
	path := os.Getenv("KHANEH_RECORDS_PATH")
	if path == "" {
		path = "../khaneh-portraits/assets/portraits/records.json"
	}
	people, err := loadPeople(path)
	if err != nil {
		log.Fatalf("Load records (run from outputs/khaneh-api or set KHANEH_RECORDS_PATH): %v", err)
	}
	address := os.Getenv("KHANEH_API_ADDR")
	if address == "" {
		address = "127.0.0.1:8082"
	}
	listener, err := net.Listen("tcp", address)
	if err != nil {
		log.Fatal(err)
	}
	server := &http.Server{Handler: newHandler(people), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 10 * time.Second, IdleTimeout: 60 * time.Second}
	log.Printf("Khaneh API listening at http://%s with %d people", listener.Addr(), len(people))
	log.Fatal(server.Serve(listener))
}
