package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestAIProxy(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/ask" || r.URL.Query().Get("q") != "Who loved football?" || r.URL.Query().Get("person_id") != "mani" {
			t.Error("forwarded request changed")
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"answered","answer":"Mani","sources":[]}`))
	}))
	defer upstream.Close()
	t.Setenv("KHANEH_AI_URL", upstream.URL)
	handler := newHandler(nil)
	for _, tc := range []struct {
		path   string
		status int
	}{
		{"/api/ask?q=Who+loved+football%3F&person_id=mani", 200},
		{"/api/ask?q=+", 400}, {"/api/ask", 400},
	} {
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest("GET", tc.path, nil))
		if w.Code != tc.status {
			t.Fatalf("%s: %d", tc.path, w.Code)
		}
	}
	upstream.Close()
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("GET", "/api/ask?q=hello", nil))
	if w.Code != 503 {
		t.Fatalf("offline returned %d", w.Code)
	}
}

func TestAIInvalidAndTimeout(t *testing.T) {
	for _, slow := range []bool{false, true} {
		upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if slow {
				time.Sleep(50 * time.Millisecond)
			}
			w.Write([]byte("not json"))
		}))
		client := &http.Client{Timeout: 10 * time.Millisecond}
		w := httptest.NewRecorder()
		aiHandler(client, upstream.URL, "/ask")(w, httptest.NewRequest("GET", "/api/ask?q=hello", nil))
		expected := 502
		if slow {
			expected = 503
		}
		if w.Code != expected {
			t.Fatalf("got %d want %d", w.Code, expected)
		}
		upstream.Close()
	}
}
