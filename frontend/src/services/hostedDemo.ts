import type { Network, Trusted, Settings, Event, Metric } from "../types";
const networks: Network[] = [
 {ssid:"Home_5G",bssid:"02:00:00:00:00:01",signal_strength:94,rssi:-42,security:"WPA2-Personal",band:"5 GHz",channel:36,connected:false,trusted:false,trusted_id:null,quality:"Excellent",score:null},
 {ssid:"Home_2G",bssid:"02:00:00:00:00:02",signal_strength:78,rssi:-61,security:"WPA2-Personal",band:"2.4 GHz",channel:6,connected:false,trusted:false,trusted_id:null,quality:"Good",score:null},
 {ssid:"OfficeWiFi",bssid:"02:00:00:00:00:03",signal_strength:86,rssi:-54,security:"WPA3-Personal",band:"5 GHz",channel:44,connected:false,trusted:false,trusted_id:null,quality:"Very Good",score:null},
 {ssid:"CafeGuest",bssid:"02:00:00:00:00:04",signal_strength:46,rssi:-77,security:"Open",band:"2.4 GHz",channel:11,connected:false,trusted:false,trusted_id:null,quality:"Weak",score:null},
];
let trusted: Trusted[] = [];
const events: Event[] = [];
const metrics: Metric[] = [];
let current: Network|null = null;
let since = 0;
let sampled = 0;
let settings: Settings = {auto_connect:false,smart_roaming:true,scan_interval:10,monitoring_interval:5,history_interval:30,minimum_signal:25,switch_threshold:15,sustain_seconds:15,roaming_cooldown:60,preferred_network:null,weights:{signal:.55,connectivity:.2,latency:.15,stability:.1}};
function audit(event:string,ssid:string|null=null){events.unshift({id:Date.now()+events.length,ssid,event,detail:"Browser simulation",timestamp:new Date().toISOString()});events.splice(500);}
function scan(){
 return networks.map(n=>{
  const t=trusted.find(t=>t.ssid===n.ssid&&t.security===n.security&&(!t.bssid||t.bssid===n.bssid));
  const w=settings.weights;
  const score=t?Math.min(100,n.signal_strength*w.signal+100*w.connectivity+90*w.latency+95*w.stability+t.priority+(settings.preferred_network===t.id?5:0)):null;
  return {...n,connected:current?.bssid===n.bssid,trusted:!!t,trusted_id:t?.id||null,score:score===null?null:Math.round(score*10)/10};
 }).sort((a,b)=>(b.score??-1)-(a.score??-1));
}
function connect(id:string){
 const t=trusted.find(t=>t.id===id);
 const n=scan().find(n=>n.trusted_id===id);
 if(!t||!n)throw new Error("Authorize a visible demo network first.");
 if(current?.bssid===n.bssid)return;
 if(current){audit("disconnected",current.ssid);audit("switched",n.ssid);}
 current=n;since=Date.now();sampled=0;t.last_connected_at=new Date().toISOString();audit("connected",n.ssid);
}
function tick(){
 if(settings.auto_connect&&!current){
  const n=scan().find(n=>n.trusted_id&&n.signal_strength>=settings.minimum_signal&&trusted.some(t=>t.id===n.trusted_id&&t.auto_connect_enabled));
  if(n)connect(n.trusted_id!);
 }
 if(current&&Date.now()-sampled>=settings.history_interval*1000){
  sampled=Date.now();
  const n=scan().find(n=>n.connected)!;
  metrics.push({id:sampled,ssid:n.ssid,signal_strength:n.signal_strength,score:n.score,latency_ms:20,internet_available:true,timestamp:new Date().toISOString()});
  if(metrics.length>500)metrics.shift();
 }
}
export async function demoApi<T>(path:string,method:string,body?:unknown):Promise<T>{
 const route=path.split("?")[0];
 const value=body as Record<string,unknown>|undefined;
 let result:unknown={ok:true};
 if(route==="/wifi/trusted"&&method==="POST"){
  if(value?.authorized!==true)throw new Error("Explicit authorization is required.");
  const ssid=String(value.ssid||"");
  if(!networks.some(n=>n.ssid===ssid&&n.security===value.security))throw new Error("Choose one of the visible simulation networks.");
  if(trusted.some(t=>t.ssid===ssid&&t.bssid===value.bssid))throw new Error("Network is already trusted.");
  const n:Trusted={id:crypto.randomUUID(),ssid,bssid:String(value.bssid||""),security:String(value.security),auto_connect_enabled:value.auto_connect_enabled!==false,priority:Number(value.priority||0),created_at:new Date().toISOString(),last_connected_at:null};
  // Intentionally never copy, save or send a password in the hosted demo.
  trusted.push(n);audit("trusted_added",ssid);result=n;
 }else if(route.startsWith("/wifi/trusted/")){
  const id=route.split("/").pop()!;const t=trusted.find(t=>t.id===id);
  if(!t)throw new Error("Trusted network not found.");
  if(method==="DELETE"){trusted=trusted.filter(t=>t.id!==id);if(settings.preferred_network===id)settings.preferred_network=null;audit("trusted_removed",t.ssid);}
  else if(method==="PATCH"){if(typeof value?.auto_connect_enabled==="boolean")t.auto_connect_enabled=value.auto_connect_enabled;if(typeof value?.priority==="number")t.priority=Math.max(-10,Math.min(10,value.priority));audit("trusted_updated",t.ssid);result=t;}
 }else if(route.startsWith("/wifi/connect/")){connect(route.split("/").pop()!);}
 else if(route==="/wifi/disconnect"){if(current)audit("disconnected",current.ssid);current=null;settings.auto_connect=false;}
 else if(route.startsWith("/wifi/auto-connect/")){settings.auto_connect=route.endsWith("/enable");audit("settings_updated");}
 else if(route==="/settings"&&method==="PUT"){
  const next=body as Settings;const weights=Object.values(next.weights);const sum=weights.reduce((a,b)=>a+b,0);
  if(!sum||weights.some(w=>!Number.isFinite(w)||w<0))throw new Error("Use non-negative ranking weights with a positive total.");
  settings={...next,weights:Object.fromEntries(Object.entries(next.weights).map(([k,v])=>[k,v/sum]))};audit("settings_updated");result=settings;
 }
 tick();
 if(method==="GET"){
  if(route==="/wifi/current")result={network:current?scan().find(n=>n.connected):null,connectivity:current?{internet_available:true,latency_ms:20,dns_working:true,gateway_reachable:true,packet_loss_percent:null,probe:"Browser simulation"}:null,measurement_age_seconds:current?0:null,connection_duration_seconds:current?Math.floor((Date.now()-since)/1000):0,auto_connect:settings.auto_connect,mode:"simulation"};
  else if(route==="/wifi/scan")result=scan();
  else if(route==="/wifi/trusted")result=trusted;
  else if(route==="/wifi/history")result=events;
  else if(route==="/wifi/metrics")result={connections:metrics,signals:metrics};
  else if(route==="/settings")result=settings;
  else if(route==="/system/status")result={mode:"simulation",monitoring:true,adapter:"Browser demo",error:null,credential_storage:"No credentials collected",version:"1.0.0"};
 }
 return structuredClone(result) as T;
}
