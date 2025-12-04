package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/account_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class AccountBad {

  private static Lock m = new ReentrantLock();
  private static int x, y, z, balance;
  private static boolean deposit_done = false, withdraw_done = false;

  private static void deposit() {
    m.lock();
    try {
      balance = balance + y;
      deposit_done = true;
    } finally {
      m.unlock();
    }
  }

  private static void withdraw() {
    m.lock();
    try {  
      balance = balance - z;
      withdraw_done = true;
    } finally {
      m.unlock();
    }
  }

  private static void check_result() {
    m.lock();
    try {
      if (deposit_done && withdraw_done)
        assert balance == (x - y) - z; /* BAD */
    } finally {
      m.unlock(); 
    }
  }

  public static void main(String[] args) {
    x = 1;
    y = 2;
    z = 4;
    balance = x;

    Thread t3 = new Thread(() -> check_result());
    Thread t1 = new Thread(() -> deposit());
    Thread t2 = new Thread(() -> withdraw());
    
    t3.start();
    t1.start();
    t2.start();
  }
}