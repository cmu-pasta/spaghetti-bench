// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/twostage_100_bad.c
package cmu.pasta.fray.benchmark.sctbench.cs.origin;

import java.util.concurrent.locks.ReentrantLock;

public class Twostage100Bad {
  static int iTThreads = 99;  
  static int iRThreads = 1;
  static int data1Value = 0;
  static int data2Value = 0;
  static ReentrantLock data1Lock;
  static ReentrantLock data2Lock;
  
  static void lock(ReentrantLock lock) {
    lock.lock();
  }
  
  static void unlock(ReentrantLock lock) {
    lock.unlock();
  }

  static void funcA() {
    lock(data1Lock);
    data1Value = 1;
    unlock(data1Lock);
    
    lock(data2Lock);
    data2Value = data1Value + 1;
    unlock(data2Lock);
  }
  
  static void funcB() {
    int t1 = -1;
    int t2 = -1;

    lock(data1Lock);
    if (data1Value == 0) {
      unlock(data1Lock);
      return;
    }
    t1 = data1Value;
    unlock(data1Lock);

    lock(data2Lock);  
    t2 = data2Value;
    unlock(data2Lock);

    if (t2 != (t1 + 1)) {
      System.err.println("Bug found!");
      assert false;
    }
  }
  
  public static void main(String[] args) {
    iTThreads = 99;
    iRThreads = 1;
    data1Value = 0;
    data2Value = 0;

    data1Lock = new ReentrantLock();
    data2Lock = new ReentrantLock();
    
    Thread[] tPool = new Thread[iTThreads];
    Thread[] rPool = new Thread[iRThreads];
    
    for (int i = 0; i < iTThreads; i++) {
      tPool[i] = new Thread(() -> funcA());
      tPool[i].start();
    }
    
    for (int i = 0; i < iRThreads; i++) {
      rPool[i] = new Thread(() -> funcB());
      rPool[i].start();  
    }
    
    for (Thread t : tPool) {
      try {
        t.join();
      } catch (InterruptedException e) {
        System.err.println("Thread interrupted");
        throw new RuntimeException();
      }
    }
    
    for (Thread t : rPool) {
      try {
        t.join();
      } catch (InterruptedException e) {
        System.err.println("Thread interrupted");  
        throw new RuntimeException();
      }
    }
  }
}