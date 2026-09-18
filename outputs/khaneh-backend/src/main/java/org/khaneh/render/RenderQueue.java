package org.khaneh.render;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import java.time.*;
import java.util.*;

@Service
public class RenderQueue {
    private final JdbcTemplate db;
    public RenderQueue(JdbcTemplate db) { this.db=db; }
    private OffsetDateTime now() { return OffsetDateTime.now(ZoneOffset.UTC); }
    public Map<String,Object> get(String id) {
        var rows=db.queryForList("SELECT * FROM render_jobs WHERE id=?", id);
        if(rows.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Job not found");
        return rows.getFirst();
    }
    public Map<String,Object> view(Map<String,Object> job) {
        var result=new LinkedHashMap<String,Object>();
        for(String key:List.of("id","asset_id","preset","device","status","progress","attempts","renderer","created_at","started_at","finished_at","elapsed_ms","error")) result.put(key,job.get(key));
        var filenames=Objects.toString(job.get("artifacts"), "");
        result.put("artifacts",filenames.isEmpty()?List.of():Arrays.stream(filenames.split(",")).map(name->Map.of("name",name,"url","/api/render/jobs/"+job.get("id")+"/artifacts/"+name)).toList());
        return result;
    }
    public List<Map<String,Object>> list() { return db.queryForList("SELECT * FROM render_jobs ORDER BY created_at DESC LIMIT 30").stream().map(this::view).toList(); }
    public Map<String,Object> create(String asset,String preset,String device) {
        if(!"hamid".equals(asset)||!List.of("preview","turntable").contains(preset)||!List.of("AUTO","CPU","OPTIX","CUDA").contains(device)) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Unknown asset, preset, or device");
        String id=UUID.randomUUID().toString();
        db.update("INSERT INTO render_jobs(id,asset_id,preset,device,status,created_at) VALUES(?,?,?,?, 'QUEUED',?)",id,asset,preset,device,now());
        return view(get(id));
    }
    @Transactional
    public Map<String,Object> claim(String worker) {
        // Recover abandoned leases. A process crash does not lose a queued render.
        db.update("UPDATE render_jobs SET status=CASE WHEN attempts<2 THEN 'QUEUED' ELSE 'FAILED' END, error='Worker lease expired', lease_token=NULL, lease_until=NULL WHERE status='RUNNING' AND lease_until<?",now());
        var rows=db.queryForList("SELECT * FROM render_jobs WHERE status='QUEUED' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED");
        if(rows.isEmpty()) return null;
        String id=rows.getFirst().get("id").toString(), lease=UUID.randomUUID().toString();
        db.update("UPDATE render_jobs SET status='RUNNING',progress=0,attempts=attempts+1,worker_id=?,lease_token=?,lease_until=?,started_at=?,error=NULL WHERE id=?",worker,lease,now().plusSeconds(45),now(),id);
        return get(id);
    }
    public boolean heartbeat(String id,String lease,int progress,String renderer) {
        return db.update("UPDATE render_jobs SET lease_until=?,progress=?,renderer=? WHERE id=? AND status='RUNNING' AND lease_token=? AND lease_until>=?",now().plusSeconds(45),Math.max(0,Math.min(99,progress)),renderer,id,lease,now())==1;
    }
    public void complete(String id,String lease,String artifacts,long elapsed,String renderer) {
        if(db.update("UPDATE render_jobs SET status='SUCCEEDED',progress=100,finished_at=?,elapsed_ms=?,artifacts=?,artifact_attempt=?,renderer=?,lease_token=NULL,lease_until=NULL WHERE id=? AND status='RUNNING' AND lease_token=? AND lease_until>=?",now(),elapsed,artifacts,lease,renderer,id,lease,now())!=1) throw new ResponseStatusException(HttpStatus.CONFLICT,"Lease is no longer active");
    }
    public void fail(String id,String lease,String error) {
        if(db.update("UPDATE render_jobs SET status='FAILED',error=?,finished_at=?,lease_token=NULL,lease_until=NULL WHERE id=? AND status='RUNNING' AND lease_token=? AND lease_until>=?",error.substring(0,Math.min(error.length(),1800)),now(),id,lease,now())!=1) throw new ResponseStatusException(HttpStatus.CONFLICT,"Lease is no longer active");
    }
    public Map<String,Object> cancel(String id) {
        get(id);
        db.update("UPDATE render_jobs SET status='CANCELLED',finished_at=?,lease_token=NULL,lease_until=NULL WHERE id=? AND status IN ('QUEUED','RUNNING')",now(),id);
        return view(get(id));
    }
    @Transactional
    public void worker(String id,String devices) {
        if(db.update("UPDATE render_workers SET last_seen=?,devices=? WHERE id=?",now(),devices,id)==0) db.update("INSERT INTO render_workers(id,last_seen,devices) VALUES(?,?,?)",id,now(),devices);
    }
    public List<Map<String,Object>> workers() {return db.queryForList("SELECT id,devices,last_seen FROM render_workers WHERE last_seen>?",now().minusSeconds(30));}
}
