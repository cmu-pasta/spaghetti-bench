package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/circular_buffer_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class CircularBufferBad {
    static final int BUFFER_MAX = 10;
    static final int N = 7;
    static final int ERROR = -1; 
    static final boolean FALSE = false;
    static final boolean TRUE = true;
  
    static char[] buffer = new char[BUFFER_MAX];   /* BUFFER */
  
    static int first;         /* Pointer to the input buffer   */ 
    static int next;          /* Pointer to the output pointer */
    static int buffer_size;   /* Max amount of elements in the buffer */
  
    static boolean send;
    static boolean receive; 

    static Lock m = new ReentrantLock();
  
    static void initLog(int max) {
      buffer_size = max;
      first = 0;
      next = 0;
    }
  
    static int removeLogElement() {
      assert first >= 0;
  
      if (next > 0 && first < buffer_size) {
        first++;
        return buffer[first-1]; 
      }
      else {
        return ERROR;
      }
    }
  
    static int insertLogElement(int b) {
      if (next < buffer_size && buffer_size > 0) {
        buffer[next] = (char)b; 
        next = (next+1) % buffer_size;
        assert next < buffer_size;
      }
      else {
        return ERROR; 
      }
  
      return b;
    }
  
    static void t1() {
      for (int i=0; i<N; i++) {
        m.lock();
        try {
          if (send) {
            insertLogElement(i);
            send = FALSE;
            receive = TRUE;
          }
        } finally {
          m.unlock();
        }
      }
    }
  
    static void t2() {
      for (int i=0; i<N; i++) {
        m.lock();
        try {
          if (receive) {
            assert removeLogElement() == i; /* BAD */
            receive = FALSE; 
            send = TRUE;
          }
        } finally {
          m.unlock(); 
        }
      }
    }
  
    public static void main(String[] args) {
      Thread id1 = new Thread(() -> t1());
      Thread id2 = new Thread(() -> t2());
  
      initLog(10);
      send = TRUE;
      receive = FALSE;
 
      id1.start();
      id2.start();
  
      try {
        id1.join();
        id2.join();
      } catch (InterruptedException e) {
        e.printStackTrace();
      }
    }
}