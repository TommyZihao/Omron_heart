package cn.zihao.heartbeat;
import java.io.*;
public class DetectorReplay {
 public static void main(String[] args)throws Exception{
  Detector d=new Detector();long last=-1;int row=0;
  try(BufferedReader r=new BufferedReader(new FileReader(args[0]))){r.readLine();String line;while((line=r.readLine())!=null){String[] c=line.split(",");long seq=Long.parseLong(c[0]);int index=Integer.parseInt(c[1]);if(index==0&&last!=-1&&seq!=last+1)d=new Detector();if(d.feed(Integer.parseInt(c[2])))System.out.println(row+","+d.bpm());if(index==99)last=seq;row++;}}
 }
}
