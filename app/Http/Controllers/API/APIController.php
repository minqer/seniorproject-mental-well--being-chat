<?php

namespace App\Http\Controllers\API;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Http\Controllers\Controller;
use Predis\Client;

class APIController extends Controller
{
    public $seperator = '$#^&^#$';
     public function send(Request $request,$sendId,$receiveId,$msg)
     {
         
         $token = $request->input('token');
         $id = $request->input('id');
         if(!$this->checkToken($token,$id)){
             return response()->json(['error' => 'Not authorized.'],403);
         }
    
         if($sendId > $receiveId){
             $first = $receiveId;
             $last = $sendId;
         }
         else{
             $first = $sendId;
             $last = $receiveId;
         }
         
         $client = new \Predis\Client();
         $ms = round(microtime(true)*1000);
         $messageid = $client->incr('messageid');
         $client ->lpush("$first". $this->seperator ."$last", "$sendId". $this->seperator ."$msg". $this->seperator ."$ms". $this->seperator ."$messageid");
         return response()->json(array(
                                       'result' => 'ok',
                                       'message' => 'message is sent',
                                       'data' => null
                                       ))->header('Access-Control-Allow-Origin', '*');;
     }
    
    public function get(Request $request,$sendId,$receiveId,$lastn)
    {
        
        $token = $request->input('token');
        $id = $request->input('id');
        if(!$this->checkToken($token,$id)){
            return response()->json(['error' => 'Not authorized.'],403);
        }
        
        if($sendId > $receiveId){
            $first = $receiveId;
            $last = $sendId;
        }
        else{
            $first = $sendId;
            $last = $receiveId;
        }
        
        $client = new \Predis\Client();
        $messages = $client ->lrange("$first". $this->seperator ."$last", 0,$lastn);
        
        $newMessages = array();
        foreach ($messages as $message) {
            $tmp = explode($this->seperator, $message);
            $newMessage = array(
                                'sender' => $tmp[0],
                                'receive' => $tmp[0] == $sendId ? $receiveId : $sendId,
                                'textdata' => $tmp[1],
                                'time' => $tmp[2],
                                );
            
            $newMessages[] = $newMessage;
        }
        return response()->json(array(
                                      'result' => 'ok',
                                      'message' => '',
                                      'data' => array_reverse($newMessages)
                                      ))->header('Access-Control-Allow-Origin', '*');;
    }

    
    public function save2db(){
            $client = new \Predis\Client();
            $keys = $client->keys('*');
        
        foreach($keys as $key){
            if($key != "messageid"){
                $messages = $client->lrange($key,0,-1);
                
                $tmp = explode($this->seperator,$key);
                $maxid = DB::select('SELECT COALESCE(max(id),0) as maxid FROM `datalog` where (sender =? and receive =?) or (sender =? and receive =?) ', [$tmp[0],$tmp[1],$tmp[1],$tmp[0]]);
                
                $maxid = $maxid[0];
                $maxid = $maxid->maxid;
                
                foreach($messages as $message){
                        $parts = explode($this->seperator,$message);
                        $sender = $parts[0];
                        $message = $parts[1];
                        $time = $parts[2];
                        $messageid = $parts[3];
                    if($sender == $tmp[0]){
                        $receiver = $tmp[1];
                    }
                    else{
                        $receiver = $tmp[0];
                    }
                 
                    if($messageid > $maxid){
                        DB::insert('insert into datalog (id,sender, receive, textdata, time) values (?,?,?, ?, ?)', [$messageid,$sender,$receiver,$message,$time]);
                    }
                }
            }
            
        }
        
        return response("done");
         }
    
     public function meditateStart(Request $request,$userId,$packageId){
         $start = round(microtime(true)*1000);
         DB::insert('insert into meditate_history (userid,start, stop, package) values (?,?,?,?)', [$userId,$start,-1,$packageId]);
         $insertedId = DB::select('SELECT LAST_INSERT_ID() as last_id');
         $insertedId = $insertedId[0];
         $insertedId = $insertedId->last_id;
         
         return response()->json(array(
                'result' => 'OK',
                'meditate_id' => $insertedId
        ));
     }
    public function meditateStop(Request $userId, $insertedId){
        $stop = round(microtime(true)*1000);
        DB::update('update meditate_history set stop = (?) WHERE id = (?)', [$stop,$insertedId]);
        
        return response()->json(array(
               'result' => 'OK',
               'meditate_id' => $insertedId
        ));

    }
    
   
    private function checkToken($token,$id){
        return $token == '1234'&& $id == 'qwerty';
    }
    }

