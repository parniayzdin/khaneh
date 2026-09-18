package main

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRoutes(t *testing.T) {
	people, err := loadPeople("../khaneh-portraits/assets/portraits/records.json")
	if err != nil {
		t.Fatal(err)
	}
	handler := newHandler(people)
	for _, tc := range []struct {
		method, path string
		status       int
	}{{"GET", "/", 200}, {"GET", "/health", 200}, {"GET", "/api/people", 200}, {"GET", "/api/people/mani", 200}, {"GET", "/api/people/missing", 404}, {"POST", "/api/people", 405}, {"DELETE", "/api/people/mani", 405}, {"GET", "/missing", 404}} {
		t.Run(tc.method+tc.path, func(t *testing.T) {
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, httptest.NewRequest(tc.method, tc.path, nil))
			if w.Code != tc.status {
				t.Fatalf("got %d want %d", w.Code, tc.status)
			}
			if tc.status == 200 && !json.Valid(w.Body.Bytes()) {
				t.Fatal("invalid JSON")
			}
		})
	}
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("GET", "/api/people", nil))
	var got []Person
	if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil || len(got) != len(people) {
		t.Fatal("records lost")
	}
	for _, origin := range []string{"http://localhost:4173", "http://127.0.0.1:4173", "https://untrusted.example"} {
		req := httptest.NewRequest("GET", "/api/people", nil)
		req.Header.Set("Origin", origin)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		expected := origin
		if strings.Contains(origin, "untrusted") {
			expected = ""
		}
		if w.Header().Get("Access-Control-Allow-Origin") != expected {
			t.Fatal("incorrect CORS")
		}
	}
}
func TestInvalidRecords(t *testing.T) {
	for _, data := range []string{"broken", "[]", `[{"id":"x"}]`} {
		path := filepath.Join(t.TempDir(), "records.json")
		os.WriteFile(path, []byte(data), 0600)
		if _, err := loadPeople(path); err == nil {
			t.Fatal("accepted invalid records")
		}
	}
	if _, err := loadPeople("missing.json"); err == nil {
		t.Fatal("accepted missing file")
	}
}
