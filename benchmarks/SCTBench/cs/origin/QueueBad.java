package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/queue_bad.c

import java.util.concurrent.locks.ReentrantLock;

public class QueueBad {
  static final int SIZE = 20;
  static final int EMPTY = -1;
  static final int FULL = -2;
  static final boolean FALSE = false;
  static final boolean TRUE = true;

  static class QType {
    int[] element = new int[SIZE];
    int head;    
    int tail;
    int amount;
  }

  static ReentrantLock mutex = new ReentrantLock();
  static int[] stored_elements = new int[SIZE];
  static boolean enqueue_flag, dequeue_flag;
  static QType queue = new QType();

  static void init(QType q) {
    q.head = 0;
    q.tail = 0;
    q.amount = 0;
  }

  static int empty(QType q) {
    if (q.head == q.tail) {
      System.out.println("queue is empty");
      return EMPTY; 
    } else {
      return 0;
    }
  }

  static int full(QType q) {
    if (q.amount == SIZE) {
      System.out.println("queue is full");
      return FULL;
    } else {
      return 0;
    }
  }

  static int enqueue(QType q, int x) {
    q.element[q.tail] = x;
    q.amount++;
    if (q.tail == SIZE) {
      q.tail = 1;
    } else {
      q.tail++;
    }
    return 0;
  }

  static int dequeue(QType q) {
    int x;
    x = q.element[q.head];
    q.amount--;
    if (q.head == SIZE) {
      q.head = 1; 
    } else {
      q.head++; 
    }
    return x;
  }

  public static void main(String[] args) {
    enqueue_flag = TRUE;
    dequeue_flag = FALSE;
    mutex = new ReentrantLock();

    init(queue);

    assert empty(queue) == EMPTY;

    Thread t1 = new Thread(() -> {
      int value = 0; 
      int i;

      mutex.lock();
      assert enqueue(queue, value) == 0;
      stored_elements[0] = value;
      assert empty(queue) == 0;
      mutex.unlock();

      for (i=0; i<(SIZE-1); i++) {
        mutex.lock();
        if (enqueue_flag) {
          value++;
          enqueue(queue, value);
          stored_elements[i+1] = value;
          enqueue_flag = FALSE;
          dequeue_flag = TRUE;
        }
        mutex.unlock();
      }
    });

    Thread t2 = new Thread(() -> {
      int i;
      for (i=0; i<SIZE; i++) {
        mutex.lock();
        if (dequeue_flag) {
          assert dequeue(queue) == stored_elements[i]; // BAD
          dequeue_flag = FALSE;
          enqueue_flag = TRUE;
        }
        mutex.unlock();
      }
    });

    t1.start();
    t2.start();

    try {
      t1.join();
      t2.join();
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
  }
}