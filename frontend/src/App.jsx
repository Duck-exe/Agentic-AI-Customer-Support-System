import React,{useEffect,useRef,useState} from "react";
import {api} from "./api";

const starters=[
 "I paid yesterday but Premium is still locked.",
 "What is your refund policy?",
 "How do I reset my password?",
 "Compare Basic and Premium plans."
];

function Auth({onDone}){
 const [mode,setMode]=useState("login"),[email,setEmail]=useState("demo@example.com"),
 [password,setPassword]=useState("password123"),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e){
   e.preventDefault(); setBusy(true); setError("");
   try{
     const {data}=await api.post(`/auth/${mode}`,{email,password});
     localStorage.setItem("support_token",data.access_token); onDone();
   }catch(err){setError(err.response?.data?.detail||"Request failed")}
   finally{setBusy(false)}
 }
 return <div className="authShell">
   <div className="brandPanel">
     <div className="logo">TM</div><h1>TechMart AI Support</h1>
     <p>Multi-agent customer service powered by RAG, semantic retrieval and specialized AI agents.</p>
     <div className="agentGrid">{["Billing","Technical","Product","Complaint","FAQ"].map(x=><span key={x}>{x}</span>)}</div>
   </div>
   <form className="authCard" onSubmit={submit}>
     <div className="eyebrow">Secure customer portal</div><h2>{mode==="login"?"Welcome back":"Create account"}</h2>
     <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label>
     <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} required/></label>
     {error&&<div className="error">{error}</div>}
     <button className="primary" disabled={busy}>{busy?"Please wait...":mode==="login"?"Sign in":"Register"}</button>
     <button type="button" className="linkBtn" onClick={()=>setMode(mode==="login"?"register":"login")}>
       {mode==="login"?"Need an account? Register":"Already registered? Sign in"}
     </button>
   </form>
 </div>
}

export default function App(){
 const [ready,setReady]=useState(Boolean(localStorage.getItem("support_token")));
 const [conversations,setConversations]=useState([]),[conversationId,setConversationId]=useState(null);
 const [messages,setMessages]=useState([]),[input,setInput]=useState(""),[busy,setBusy]=useState(false),[analytics,setAnalytics]=useState(null);
 const endRef=useRef();

 async function refreshSidebar(){
   const [{data:convs},{data:stats}]=await Promise.all([api.get("/conversations"),api.get("/analytics")]);
   setConversations(convs); setAnalytics(stats);
 }
 function logout(){localStorage.removeItem("support_token");setReady(false);setMessages([]);setConversationId(null)}
 useEffect(()=>{if(ready) refreshSidebar().catch(logout)},[ready]);
 useEffect(()=>endRef.current?.scrollIntoView({behavior:"smooth"}),[messages,busy]);

 async function openConversation(id){
   const {data}=await api.get(`/conversations/${id}`); setConversationId(id); setMessages(data.messages);
 }
 function newChat(){setConversationId(null);setMessages([]);setInput("")}
 async function send(text=input){
   const clean=text.trim(); if(!clean||busy)return;
   setInput(""); setMessages(m=>[...m,{role:"user",content:clean}]); setBusy(true);
   try{
     const {data}=await api.post("/chat",{message:clean,conversation_id:conversationId});
     setConversationId(data.conversation_id);
     setMessages(m=>[...m,{role:"assistant",content:data.answer,agents:data.agents,sources:data.retrieved_sources,
       escalated:data.escalated,response_time_ms:data.response_time_ms}]);
     await refreshSidebar();
   }catch(err){
     setMessages(m=>[...m,{role:"assistant",content:err.response?.data?.detail||"The support service could not process the request."}]);
   }finally{setBusy(false)}
 }
 if(!ready)return <Auth onDone={()=>setReady(true)}/>;
 return <div className="appShell">
   <aside>
     <div className="sideBrand"><div className="logo small">TM</div><strong>TechMart AI</strong></div>
     <button className="newChat" onClick={newChat}>+ New conversation</button>
     <div className="sideLabel">Recent</div>
     <div className="conversationList">{conversations.map(c=>
       <button key={c.id} className={c.id===conversationId?"conv active":"conv"} onClick={()=>openConversation(c.id)}>
         <span>{c.title}</span><small>#{c.id}</small>
       </button>)}</div>
     {analytics&&<div className="stats"><div><b>{analytics.conversations}</b><span>Chats</span></div><div><b>{analytics.open_tickets}</b><span>Open tickets</span></div></div>}
     <button className="logout" onClick={logout}>Sign out</button>
   </aside>
   <main>
     <header><div><div className="eyebrow">Multi-Agent Support Orchestrator</div><h2>{conversationId?`Conversation #${conversationId}`:"How can we help?"}</h2></div><div className="status"><i/> RAG knowledge online</div></header>
     <section className="chat">
       {messages.length===0&&<div className="welcome"><div className="heroIcon">AI</div><h1>One chat. Five specialists.</h1>
         <p>Your request is classified, routed to the right agent, grounded in company documents and remembered throughout the conversation.</p>
         <div className="starterGrid">{starters.map(s=><button key={s} onClick={()=>send(s)}>{s}</button>)}</div></div>}
       {messages.map((m,i)=><div className={`msgRow ${m.role}`} key={i}><div className="avatar">{m.role==="user"?"You":"AI"}</div>
         <div className="msgWrap"><div className="bubble">{m.content}</div>
           {m.agents?.length>0&&<div className="meta">{m.agents.map(a=><span className="chip" key={a}>{a} agent</span>)}
             {m.escalated&&<span className="chip warn">human escalation</span>}
             {m.response_time_ms?<span className="latency">{Math.round(m.response_time_ms)} ms</span>:null}</div>}
           {m.sources?.length>0&&<details><summary>Retrieved sources</summary>{m.sources.map(s=><div key={s}>{s}</div>)}</details>}
         </div></div>)}
       {busy&&<div className="msgRow assistant"><div className="avatar">AI</div><div className="typing"><span/><span/><span/></div></div>}
       <div ref={endRef}/>
     </section>
     <footer><div className="composer"><textarea value={input} onChange={e=>setInput(e.target.value)}
       placeholder="Ask about billing, products, technical support, policies or complaints..."
       onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}}}/>
       <button onClick={()=>send()} disabled={busy||!input.trim()}>Send</button></div>
       <small>AI answers are grounded in the TechMart knowledge base. Complex cases can be escalated.</small></footer>
   </main>
 </div>
}
