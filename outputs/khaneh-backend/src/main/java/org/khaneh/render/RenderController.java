package org.khaneh.render;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.io.IOException;
import java.util.*;

@RestController
public class RenderController {
    private final RenderQueue queue;
    private final Path storage;
    private final String token;
    public RenderController(RenderQueue queue,@Value("${khaneh.storage}")String storage,@Value("${khaneh.token-file}")String tokenFile) throws IOException {
        this.queue=queue; this.storage=Path.of(storage).toAbsolutePath().normalize(); Files.createDirectories(this.storage);
        var path=Path.of(tokenFile); Files.createDirectories(path.toAbsolutePath().getParent());
        if(!Files.exists(path)) Files.writeString(path,UUID.randomUUID()+"-"+UUID.randomUUID(),StandardOpenOption.CREATE_NEW);
        this.token=Files.readString(path).trim();
    }
    record Submit(@NotBlank String assetId,@NotBlank String preset,@NotBlank String device){}
    record Worker(@Pattern(regexp="[a-zA-Z0-9_-]{1,80}") @NotNull String workerId,@NotNull @Size(max=500) String devices){}
    record Claim(@Pattern(regexp="[a-zA-Z0-9_-]{1,80}") @NotNull String workerId){}
    record Heartbeat(@NotBlank String leaseToken,@Min(0) @Max(99) int progress,@NotNull @Size(max=120)String renderer){}
    record Finish(@NotBlank String leaseToken,@NotNull @Size(min=1,max=6)List<String> artifacts,@Min(0)long elapsedMs,@NotNull @Size(max=120)String renderer){}
    record Failure(@NotBlank String leaseToken,@NotBlank @Size(max=1800)String error){}
    private void authorize(String value) { if(value==null||!MessageDigest.isEqual(token.getBytes(StandardCharsets.UTF_8),value.getBytes(StandardCharsets.UTF_8))) throw new ResponseStatusException(HttpStatus.UNAUTHORIZED,"Worker authentication required"); }
    @GetMapping("/api/render/health") public Map<String,Object> health(){return Map.of("status","UP","storage","LOCAL","workers",queue.workers());}
    @GetMapping("/api/render/jobs") public List<Map<String,Object>> jobs(){return queue.list();}
    @PostMapping(value="/api/render/jobs",consumes=MediaType.APPLICATION_JSON_VALUE) @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String,Object> submit(@Valid @RequestBody Submit request){return queue.create(request.assetId(),request.preset(),request.device());}
    @GetMapping("/api/render/jobs/{id}") public Map<String,Object> job(@PathVariable String id){return queue.view(queue.get(id));}
    @PostMapping("/api/render/jobs/{id}/cancel") public Map<String,Object> cancel(@PathVariable String id){return queue.cancel(id);}
    @GetMapping("/api/render/jobs/{id}/artifacts/{name}") public ResponseEntity<FileSystemResource> artifact(@PathVariable String id,@PathVariable String name){
        var job=queue.get(id);
        if(!"SUCCEEDED".equals(job.get("status"))||!Arrays.asList(Objects.toString(job.get("artifacts"),"").split(",")).contains(name)) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Artifact not found");
        var file=safeArtifact(id,Objects.toString(job.get("artifact_attempt"),""),name);
        if(!Files.isRegularFile(file)) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Artifact not found");
        return ResponseEntity.ok().contentType(MediaType.IMAGE_PNG).header("X-Content-Type-Options","nosniff").body(new FileSystemResource(file));
    }
    private Path safeArtifact(String id,String attempt,String name){
        if(!id.matches("[0-9a-f-]{36}")||!attempt.matches("[0-9a-f-]{36}")||!name.matches("frame-[0-9]{3}\\.png")) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Invalid artifact name");
        Path file=storage.resolve(id).resolve(attempt).resolve(name).normalize();
        if(!file.startsWith(storage)||Files.isSymbolicLink(file)||Files.isSymbolicLink(file.getParent())||Files.isSymbolicLink(file.getParent().getParent())) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Invalid artifact path");
        return file;
    }
    @PostMapping("/api/internal/workers") public void register(@RequestHeader(value="X-Worker-Token",required=false)String auth,@Valid @RequestBody Worker w){authorize(auth);queue.worker(w.workerId(),w.devices());}
    @PostMapping("/api/internal/jobs/claim") public ResponseEntity<Map<String,Object>> claim(@RequestHeader(value="X-Worker-Token",required=false)String auth,@Valid @RequestBody Claim claim){authorize(auth);var job=queue.claim(claim.workerId());return job==null?ResponseEntity.noContent().build():ResponseEntity.ok(job);}
    @PostMapping("/api/internal/jobs/{id}/heartbeat") public Map<String,Boolean> heartbeat(@RequestHeader(value="X-Worker-Token",required=false)String auth,@PathVariable String id,@Valid @RequestBody Heartbeat h){authorize(auth);return Map.of("active",queue.heartbeat(id,h.leaseToken(),h.progress(),h.renderer()));}
    @PostMapping("/api/internal/jobs/{id}/complete") public void complete(@RequestHeader(value="X-Worker-Token",required=false)String auth,@PathVariable String id,@Valid @RequestBody Finish f){
        authorize(auth);
        int expected="turntable".equals(queue.get(id).get("preset"))?6:1;
        if(f.artifacts().size()!=expected||new HashSet<>(f.artifacts()).size()!=expected) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Incomplete artifact set");
        for(String name:f.artifacts()) if(!Files.isRegularFile(safeArtifact(id,f.leaseToken(),name)))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Missing artifact");
        queue.complete(id,f.leaseToken(),String.join(",",f.artifacts()),f.elapsedMs(),f.renderer());
    }
    @PostMapping("/api/internal/jobs/{id}/fail") public void fail(@RequestHeader(value="X-Worker-Token",required=false)String auth,@PathVariable String id,@Valid @RequestBody Failure f){authorize(auth);queue.fail(id,f.leaseToken(),f.error());}
}
