<?php

namespace App\Http\Controllers\API;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Http\Controllers\Controller;
use Predis\Client;

class APIController extends Controller
{
    public $seperator = '$#^&^#$';

    public function list(){
        return response()->json([
            array(
                'desc' => 'start meditate',
                'url' => "/miniapp/meditate/start/{userId}/{packageId}",
            ),
            array(
                'desc' => 'stop meditate',
                'url' => "/miniapp/meditate/stop/{userId}/{insertedId}",
            ),
        ]);
    }

    public function send_get(Request $request,$sendId,$receiveId,$message){
        return $this->send($request,$sendId,$receiveId,$message);
    }

    public function send_post(Request $request,$sendId,$receiveId)
    {
        $message = str_replace('$#^&^#$','...',$request->input('msg'));
        return $this->send($request,$sendId,$receiveId,$message);
    }

    public function send(Request $request,$sendId,$receiveId,$message){
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
        
        $client = new \Predis\Client('tcp://localhost:6381');
        $ms = round(microtime(true)*1000);
        $messageid = $client->incr('messageid');
        $client ->lpush("$first". $this->seperator ."$last", "$sendId". $this->seperator ."$message". $this->seperator ."$ms". $this->seperator ."$messageid");
        return response()->json(array(
                                    'result' => 'ok',
                                    'message' => 'message is sent',
                                    'data' => null
                                    ))->header('Access-Control-Allow-Origin', '*');
    }
    
    public function get2(Request $request,$sendId,$receiveId,$lastn){
        $targetIndex = 10;
        get($request,$sendId,$receiveId,$lastn,$targetIndex);
    }

    public function get(Request $request,$sendId,$receiveId,$lastn,$targetIndex=0)
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
        
        $client = new \Predis\Client('tcp://localhost:6381');
        $messages = $client ->lrange("$first". $this->seperator ."$last", $targetIndex,$lastn);
        
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
    public function meditateStop(Request $request, $userId, $insertedId){
        $stop = round(microtime(true)*1000);
        DB::update('update meditate_history set stop = (?) WHERE id = (?)', [$stop,$insertedId]);
        
        $length = DB::select('select (stop-start) AS avgtime from meditate_history WHERE id = ?', [$insertedId]);
        $length = $length[0];
        $length = round($length->n/1000);
        return response()->json(array(
               'result' => 'OK',
               'meditate_id' => $length
        ));

    }
    
    public function breathStart(Request $request, $userId){
        $start = round(microtime(true)*1000);
        DB::insert('insert into breath_history (userid,start, stop) values (?,?,?)', [$userId,$start,-1]);
        $insertedId = DB::select('SELECT LAST_INSERT_ID() as last_id');
        $insertedId = $insertedId[0];
        $insertedId = $insertedId->last_id;
        
        return response()->json(array(
                                      'result' => 'OK',
                                      'breath_id' => $insertedId
                                      ));

    }
    
    public function breathStop(Request $request, $userId, $insertedId){
        $stop = round(microtime(true)*1000);
        DB::update('update breath_history set stop = (?) WHERE id = (?)', [$stop,$insertedId]);
        
        $length = DB::select('select (stop-start) AS avgtime from breath_history WHERE id = ?', [$insertedId]);
        $length = $length[0];
        $length = round($length->avgtime/1000);
        return response()->json(array(
                                      'result' => 'OK',
                                      'breath_id' => $length
                                      ));
        
    }
   
    private function checkToken($token,$id){
        return $token == '1234'&& $id == 'qwerty';
    }
    }

