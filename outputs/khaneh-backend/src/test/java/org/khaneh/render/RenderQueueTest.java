package org.khaneh.render;

import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.server.ResponseStatusException;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class RenderQueueTest {
    static final Path DATA=Path.of("target/test-data",UUID.randomUUID().toString());
    @DynamicPropertySource static void config(DynamicPropertyRegistry r){
        r.add("spring.datasource.url",()->System.getenv().getOrDefault("TEST_DB_URL","jdbc:h2:mem:tests;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1"));
        r.add("spring.datasource.username",()->System.getenv().getOrDefault("TEST_DB_USER","sa"));
        r.add("spring.datasource.password",()->System.getenv().getOrDefault("TEST_DB_PASSWORD",""));
        r.add("khaneh.storage",()->DATA.resolve("artifacts").toString());
        r.add("khaneh.token-file",()->DATA.resolve("worker.token").toString());
    }
    @Autowired RenderQueue queue;
    @Autowired JdbcTemplate db;
    @Autowired MockMvc mvc;
    @BeforeEach void clean(){db.update("DELETE FROM render_jobs");db.update("DELETE FROM render_workers");}
    String create(){return queue.create("hamid","preview","CPU").get("id").toString();}
    @Test void validatesCatalogAndPresets() throws Exception {
        mvc.perform(post("/api/render/jobs").contentType("application/json").content("{\"assetId\":\"../../secret\",\"preset\":\"preview\",\"device\":\"CPU\"}")).andExpect(status().isBadRequest());
        assertTrue(queue.list().isEmpty());
    }
    @Test void workerEndpointsRequireToken() throws Exception {
        mvc.perform(post("/api/internal/jobs/claim").contentType("application/json").content("{\"workerId\":\"stranger\"}")).andExpect(status().isUnauthorized());
    }
    @Test void onlyOneWorkerCanClaimAJob() throws Exception {
        create();
        try(var executor=Executors.newFixedThreadPool(2)){
            var latch=new CountDownLatch(1);
            var first=executor.submit(()->{latch.await();return queue.claim("one");});
            var second=executor.submit(()->{latch.await();return queue.claim("two");});
            latch.countDown();
            assertEquals(1,Arrays.asList(first.get(),second.get()).stream().filter(Objects::nonNull).count());
        }
    }
    @Test void staleWorkerCannotReportProgress(){
        String id=create();var job=queue.claim("one");
        assertFalse(queue.heartbeat(id,UUID.randomUUID().toString(),99,"fake"));
        assertTrue(queue.heartbeat(id,job.get("lease_token").toString(),42,"Cycles / CPU"));
        assertEquals(42,queue.get(id).get("progress"));
    }
    @Test void crashedWorkerRetriesOnlyOnce(){
        String id=create();var first=queue.claim("one");expire(id);
        var retry=queue.claim("two");assertEquals(2,retry.get("attempts"));
        assertNotEquals(first.get("lease_token"),retry.get("lease_token"));
        assertFalse(queue.heartbeat(id,first.get("lease_token").toString(),90,"stale"));
        expire(id);assertNull(queue.claim("three"));assertEquals("FAILED",queue.get(id).get("status"));
    }
    void expire(String id){db.update("UPDATE render_jobs SET lease_until=? WHERE id=?",OffsetDateTime.now(ZoneOffset.UTC).minusSeconds(60),id);}
    @Test void cancellationRejectsLateCompletion(){
        String id=create();var job=queue.claim("one");queue.cancel(id);
        assertThrows(ResponseStatusException.class,()->queue.complete(id,job.get("lease_token").toString(),"frame-000.png",10,"CPU"));
        assertEquals("CANCELLED",queue.get(id).get("status"));
    }
    @Test void completionChecksFilesAndPublishesOnlyFinalizedAttempt() throws Exception {
        String id=create();var job=queue.claim("one");String lease=job.get("lease_token").toString();
        String auth=Files.readString(DATA.resolve("worker.token")).trim();
        String payload="{\"leaseToken\":\""+lease+"\",\"artifacts\":[\"frame-000.png\"],\"elapsedMs\":15,\"renderer\":\"CPU\"}";
        mvc.perform(post("/api/internal/jobs/"+id+"/complete").header("X-Worker-Token",auth).contentType("application/json").content(payload)).andExpect(status().isBadRequest());
        Path output=DATA.resolve("artifacts").resolve(id).resolve(lease);Files.createDirectories(output);Files.write(output.resolve("frame-000.png"),new byte[]{(byte)137,80,78,71});
        mvc.perform(get("/api/render/jobs/"+id+"/artifacts/frame-000.png")).andExpect(status().isNotFound());
        mvc.perform(post("/api/internal/jobs/"+id+"/complete").header("X-Worker-Token",auth).contentType("application/json").content(payload)).andExpect(status().isOk());
        mvc.perform(get("/api/render/jobs/"+id+"/artifacts/frame-000.png")).andExpect(status().isOk()).andExpect(content().contentType("image/png"));
        assertFalse(queue.view(queue.get(id)).containsKey("lease_token"));
    }
    @Test void rejectsArtifactTraversal() throws Exception {
        String id=create();var job=queue.claim("one");String auth=Files.readString(DATA.resolve("worker.token")).trim();
        String payload="{\"leaseToken\":\""+job.get("lease_token")+"\",\"artifacts\":[\"../secret.png\"],\"elapsedMs\":15,\"renderer\":\"CPU\"}";
        mvc.perform(post("/api/internal/jobs/"+id+"/complete").header("X-Worker-Token",auth).contentType("application/json").content(payload)).andExpect(status().isBadRequest());
    }
}
