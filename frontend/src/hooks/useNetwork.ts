import {useCallback,useEffect,useRef,useState} from 'react'
import {snapshot} from '../services/api'
import type {Snapshot} from '../types'
export function useNetwork(){
 const [data,setData]=useState<Snapshot|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true)
 const active=useRef(false)
 const refresh=useCallback(async()=>{if(active.current)return;active.current=true;try{setData(await snapshot());setError('')}catch(e){setError(e instanceof Error?e.message:'Could not reach WiFiSense')}finally{setLoading(false);active.current=false}},[])
 useEffect(()=>{void refresh();const id=window.setInterval(()=>void refresh(),5000);return()=>clearInterval(id)},[refresh])
 return {data,error,loading,refresh}
}
