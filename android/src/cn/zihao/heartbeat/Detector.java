package cn.zihao.heartbeat;
import java.util.*;
final class Detector {
 double base=Double.NaN,lp,prev; long n,last=-1000; boolean armed=true;
 ArrayDeque<Double> energy=new ArrayDeque<>(),history=new ArrayDeque<>(),rr=new ArrayDeque<>();
 boolean feed(int x){
  n++;if(Double.isNaN(base))base=x;
  base+=.012*(x-base);lp+=.4*(x-base-lp);double delta=lp-prev;prev=lp;
  energy.add(delta*delta);if(energy.size()>10)energy.remove();
  double e=0;for(double v:energy)e+=v;e/=energy.size();history.add(e);if(history.size()>500)history.remove();
  if(history.size()<500)return false;
  double[] sorted=history.stream().mapToDouble(Double::doubleValue).sorted().toArray();
  double threshold=Math.max(4,sorted[(int)(sorted.length*.9)]*.5);
  if(e<threshold*.45)armed=true;
  if(armed&&e>threshold&&n-last>75){double r=(n-last)/250.;if(r>.3&&r<2){rr.add(r);if(rr.size()>6)rr.remove();}last=n;armed=false;return true;}
  return false;
 }
 Integer bpm(){if(rr.isEmpty())return null;double[] a=rr.stream().mapToDouble(Double::doubleValue).sorted().toArray();double m=a.length%2==1?a[a.length/2]:(a[a.length/2-1]+a[a.length/2])/2;return (int)Math.rint(60/m);}
}
