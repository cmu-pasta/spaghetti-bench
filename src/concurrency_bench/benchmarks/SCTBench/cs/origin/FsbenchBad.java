// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/fsbench_bad.c

package cmu.pasta.fray.benchmark.sctbench.cs.origin;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class FsbenchBad {

    private static final int NUMBLOCKS = 26;
    private static final int NUMINODE = 32;
    private static final int NUM_THREADS = 27;

    private static Lock[] locki = new Lock[NUMBLOCKS];
    private static Lock[] lockb = new Lock[NUMBLOCKS];
    private static int[] busy = new int[NUMBLOCKS];
    private static int[] inode = new int[NUMINODE];

    private static Thread[] threads = new Thread[NUM_THREADS];

    private static void threadRoutine(int tid) {
        assert tid >= 0 && tid < NUM_THREADS;

        int i = tid % NUMINODE;
        assert i >= 0 && i < NUMBLOCKS;
        locki[i].lock();
        if (inode[i] == 0) {
            int b = (i * 2) % NUMBLOCKS;
            for (int j = 0; j < NUMBLOCKS / 2; j++) {
                lockb[b].lock();
                if (busy[b] == 0) {
                    busy[b] = 1;
                    inode[i] = b + 1;
                    System.out.print("  ");
                    lockb[b].unlock();
                    break;
                }
                lockb[b].unlock();
                b = (b + 1) % NUMBLOCKS;
            }
        }
        assert i >= 0 && i < NUMBLOCKS;
        locki[i].unlock(); // BAD: array locki upper bound
    }

    public static void main(String[] args) {
        for (int i = 0; i < NUMBLOCKS; i++) {
            locki[i] = new ReentrantLock();
            lockb[i] = new ReentrantLock();
            busy[i] = 0;
        }

        for (int i = 0; i < NUM_THREADS; i++) {
            int finalI = i;
            threads[i] = new Thread(() -> threadRoutine(finalI));
            threads[i].start();
        }

        for (int i = 0; i < NUM_THREADS; i++) {
            try {
                threads[i].join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}