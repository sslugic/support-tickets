```typescript
let taskCounter = 1;
export function generateTaskId() {
    return `Task-${taskCounter.toString().padStart(4, '0')}`;
}
```