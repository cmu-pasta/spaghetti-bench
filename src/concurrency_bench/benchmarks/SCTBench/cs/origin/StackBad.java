package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/stack_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class StackBad {
    private static final int TRUE = 1;
    private static final int FALSE = 0;
    private static final int SIZE = 10;
    private static final int OVERFLOW = -1;
    private static final int UNDERFLOW = -2;

    private static int top = 0;
    private static int[] arr = new int[SIZE];
    private static Lock m = new ReentrantLock();
    private static boolean flag = false;

    private static void incTop() {
        top++;
    }

    private static void decTop() {
        top--;
    }

    private static int getTop() {
        return top;
    }

    private static boolean stackEmpty() {
        return (top == 0) ? true : false;
    }

    private static int push(int[] stack, int x) {
        if (top == SIZE) {
            System.out.println("stack overflow");
            return OVERFLOW;
        } else {
            stack[getTop()] = x;
            incTop();
        }
        return 0;
    }

    private static int pop(int[] stack) {
        if (getTop() == 0) {
            System.out.println("stack underflow");
            return UNDERFLOW;
        } else {
            decTop();
            return stack[getTop()];
        }
    }

    public static void main(String[] args) {
        Thread t1 = new Thread(() -> {
            for (int i = 0; i < SIZE; i++) {
                m.lock();
                try {
                    assert push(arr, i) != OVERFLOW;
                    flag = true;
                } finally {
                    m.unlock();
                }
            }
        });

        Thread t2 = new Thread(() -> {
            for (int i = 0; i < SIZE; i++) {
                m.lock();
                try {
                    if (flag)
                        assert pop(arr) != UNDERFLOW; /* BAD */
                } finally {
                    m.unlock();
                }
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