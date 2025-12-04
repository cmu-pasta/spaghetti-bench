package cmu.pasta.fray.benchmark.sctbench.chess;

// Translated from: https://github.com/mc-imperial/sctbench/blob/master/benchmarks/chess/WorkStealQueue.cpp

import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.ReentrantLock;

public class WorkStealQueue<T> {
    private static final long MaxSize = 1024 * 1024;
    private static final long InitialSize = 2; // must be a power of 2

    private volatile AtomicLong head = new AtomicLong(0); // only updated by Take
    private volatile AtomicLong tail = new AtomicLong(0); // only updated by Push and Pop
    private T[] elems; // the array of tasks
    private long mask; // the mask for taking modulus

    private final ReentrantLock lock = new ReentrantLock();

    @SuppressWarnings("unchecked")
    public WorkStealQueue(long size) {
        mask = size - 1;
        elems = (T[]) new Object[(int) size];
    }

    public WorkStealQueue() {
        this(MaxSize);
    }

    private long readV(AtomicLong v) {
        return v.get();
    }

    private void writeV(AtomicLong v, long w) {
        v.set(w);
    }

    public boolean steal(T[] result) {
        boolean found;
        lock.lock();
        try {
            long h = readV(head);
            writeV(head, h + 1);

            if (h < readV(tail)) {
                result[0] = elems[(int) (h & mask)];
                found = true;
            } else {
                writeV(head, h);
                found = false;
            }
        } finally {
            lock.unlock();
        }
        return found;
    }

    public boolean pop(T[] result) {
        long t = readV(tail) - 1;
        writeV(tail, t);

        if (readV(head) <= t) {
            result[0] = elems[(int) (t & mask)];
            return true;
        } else {
            writeV(tail, t + 1);
            return syncPop(result);
        }
    }

    private boolean syncPop(T[] result) {
        boolean found;
        lock.lock();
        try {
            long t = readV(tail) - 1;
            writeV(tail, t);
            if (readV(head) <= t) {
                result[0] = elems[(int) (t & mask)];
                found = true;
            } else {
                writeV(tail, t + 1);
                found = false;
            }
            if (readV(head) > t) {
                writeV(head, 0);
                writeV(tail, 0);
                found = false;
            }
        } finally {
            lock.unlock();
        }
        return found;
    }

    public void push(T elem) {
        long t = readV(tail);
        if (t < readV(head) + mask + 1 && t < MaxSize) {
            elems[(int) (t & mask)] = elem;
            writeV(tail, t + 1);
        } else {
            syncPush(elem);
        }
    }

    @SuppressWarnings("unchecked")
    private void syncPush(T elem) {
        lock.lock();
        try {
            long h = readV(head);
            long count = readV(tail) - h;

            h = h & mask;
            writeV(head, h);
            writeV(tail, h + count);

            if (count >= mask) {
                long newsize = (mask == 0 ? InitialSize : 2 * (mask + 1));

                assert newsize < MaxSize;

                T[] newtasks = (T[]) new Object[(int) newsize];
                for (long i = 0; i < count; i++) {
                    newtasks[(int) i] = elems[(int) ((h + i) & mask)];
                }
                elems = newtasks;
                mask = newsize - 1;
                writeV(head, 0);
                writeV(tail, count);
            }

            assert count < mask;

            long t = readV(tail);
            elems[(int) (t & mask)] = elem;
            writeV(tail, t + 1);
        } finally {
            lock.unlock();
        }
    }

    private static class ObjType {
        private int field;

        public ObjType() {
            field = 0;
        }

        public void operation() {
            field++;
        }

        public void check() {
            assert (field == 1) : "Bug found!";
        }
    }

    public static void main(String[] args) {
        int nStealers = 1;
        int nItems = 4;
        int nStealAttempts = 2;

        // if (args.length > 0) {
        // int arg1 = Integer.parseInt(args[0]);
        // if (arg1 > 0) {
        // nStealers = arg1;
        // }
        // }
        // if (args.length > 1) {
        // int arg2 = Integer.parseInt(args[1]);
        // if (arg2 > 0) {
        // nItems = arg2;
        // }
        // }
        // if (args.length > 2) {
        // int arg3 = Integer.parseInt(args[2]);
        // if (arg3 > 0) {
        // nStealAttempts = arg3;
        // }
        // }
        System.out.println("\nWorkStealQueue Test: " +
                nStealers + " stealers, " +
                nItems + " items, " +
                "and " +
                nStealAttempts + " stealAttempts");

        Thread[] handles = new Thread[nStealers];
        ObjType[] items = new ObjType[nItems];
        for (int i = 0; i < nItems; i++) {
            items[i] = new ObjType();
        }

        WorkStealQueue<ObjType> q = new WorkStealQueue<>(InitialSize);

        final int finalNStealAttempts = nStealAttempts;
        for (int i = 0; i < nStealers; i++) {
            final int idx = i;
            handles[i] = new Thread(() -> {
                ObjType[] r = new ObjType[1];
                for (int j = 0; j < finalNStealAttempts; j++) {
                    if (q.steal(r))
                        r[0].operation();
                }
            });
            handles[i].start();
        }

        for (int i = 0; i < nItems / 2; i++) {
            q.push(items[2 * i]);
            q.push(items[2 * i + 1]);

            ObjType[] r = new ObjType[1];
            if (q.pop(r))
                r[0].operation();
        }

        for (int i = 0; i < nItems / 2; i++) {
            ObjType[] r = new ObjType[1];
            if (q.pop(r))
                r[0].operation();
        }

        for (Thread handle : handles) {
            try {
                handle.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

        for (ObjType item : items) {
            item.check();
        }
    }
}