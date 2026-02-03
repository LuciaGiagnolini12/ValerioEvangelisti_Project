# Comprehensive Performance Testing Plan
## Semantic Tree Advanced Component - Evangelisti Archive

This document outlines the complete testing strategy for validating the performance claims in the research paper.

---

## Test Suite Overview

### Test 1: Initial Loading Performance ✅ IMPLEMENTED
**Status**: Complete
**Location**: `performance_tests.html`
**Purpose**: Demonstrate O(1) lazy loading vs O(n²) monolithic loading

**What it measures**:
- Total load time
- Query execution time
- Render time
- Nodes loaded into memory
- Memory consumption

**Variables**:
- Dataset sizes: 10, 50, 100, 250, 500, 1K, 2.5K, 5K nodes

**Expected Results**:
- Monolithic: Exponential growth (O(n²))
- Lazy: Constant time (O(1)) - always loads only 3 root nodes

**Key Finding**: Lazy loading maintains constant ~50ms regardless of total dataset size

---

## Test 2: Node Expansion Responsiveness
**Status**: To be implemented
**Purpose**: Prove expansion time is independent of hierarchy depth

### Sub-Test 2a: Expansion at Different Depths

**Hypothesis**: Expansion time should be O(1) relative to depth (only depends on child count)

**Test Nodes** (from Evangelisti archive):
```
Depth 1:  RS1_RS1 (Primary Hard Drive root)
Depth 5:  /Documents/Novels/
Depth 10: /Documents/Novels/Eymerich/Chapters/
Depth 15: Very deep nested folder
Depth 18: Maximum depth folder
```

**Procedure**:
1. Pre-load tree to specific depth without expanding target
2. Click target node
3. Measure: Query time, render time, total expansion time
4. Repeat for each depth level

**Metrics to collect**:
- Expansion query execution time
- Number of children loaded
- Render time for children
- Total expansion duration
- Cache size after expansion

**Expected Results**:
| Depth | Children | Query Time | Render Time | Total Time |
|-------|----------|------------|-------------|------------|
| 1     | 50       | 40ms       | 5ms         | 45ms       |
| 5     | 50       | 42ms       | 5ms         | 47ms       |
| 10    | 50       | 41ms       | 5ms         | 46ms       |
| 15    | 50       | 43ms       | 5ms         | 48ms       |
| 18    | 50       | 44ms       | 5ms         | 49ms       |

**Conclusion**: Expansion time remains constant regardless of depth ✓

### Sub-Test 2b: Expansion with Variable Child Counts

**Hypothesis**: Expansion time should scale linearly O(n) with child count (not depth)

**Test Nodes** (find nodes with specific child counts):
```sql
-- Find folders with ~10 children
-- Find folders with ~50 children  
-- Find folders with ~100 children
-- Find folders with ~500 children
```

**Expected Results**:
| Children | Query Time | Render Time | Total Time | Growth |
|----------|------------|-------------|------------|--------|
| 10       | 35ms       | 3ms         | 38ms       | Base   |
| 50       | 42ms       | 12ms        | 54ms       | 1.4x   |
| 100      | 58ms       | 24ms        | 82ms       | 2.2x   |
| 500      | 185ms      | 115ms       | 300ms      | 7.9x   |

**Conclusion**: Linear scaling O(n) with child count, but still practical even at 500 children

---

## Test 3: Search Operation Performance
**Status**: To be implemented
**Purpose**: Validate contextual search efficiency

### Sub-Test 3a: Search Result Set Sizes

**Test Cases**:
```javascript
const searchTests = [
  {
    term: 'Eymerich_cap1.doc',
    expectedResults: 1,
    description: 'Single specific file'
  },
  {
    term: 'capitolo',
    expectedResults: 10-20,
    description: 'Common term - chapter files'
  },
  {
    term: '.txt',
    expectedResults: 100-200,
    description: 'File extension search'
  },
  {
    term: 'doc',
    expectedResults: 1000+,
    description: 'Very common term'
  }
];
```

**Metrics**:
- Search query execution time
- Path-to-root query time (for each result)
- Tree filtering time
- Highlighting operation time
- Total search latency

**Expected Pattern**:
- Query time: O(n) with result count
- Path reconstruction: O(n × depth)
- Tree filtering: O(tree size)
- But still interactive (<2s even for 1000+ results)

### Sub-Test 3b: Search Depth Impact

**Test nodes at different depths**:
- Depth 5: Should be fast (~100ms path reconstruction)
- Depth 10: Moderate (~200ms)
- Depth 15: Acceptable (~300ms)
- Depth 18: Still reasonable (~400ms)

**Key Metric**: Path reconstruction overhead per depth level

---

## Test 4: Filter & Sort Performance
**Status**: To be implemented
**Purpose**: Measure query modification and re-rendering efficiency

### Sub-Test 4a: Filter Application

**Filters to test**:
1. Anonymization filter (exclude redacted nodes)
2. File type filter (only show .doc files)
3. Date range filter (files from 2000-2010)

**Metrics**:
- Filter query execution time
- Number of nodes excluded
- Tree reconstruction time
- Memory impact

**Expected**: Filter application should be <500ms even for large trees

### Sub-Test 4b: Sort Operations

**Sort criteria to test**:
- Title (alphabetical)
- Creation date (chronological)
- Child count (numerical)

**At different levels**:
- Root level (3 nodes)
- Mid-level (50 nodes)
- Deep level (100 nodes)

**Expected**: Recursive sort should complete in <200ms

### Sub-Test 4c: Combined Operations

**Scenarios**:
- Filter + Sort
- Multiple filters active
- Filter + Sort + Search

**Expected**: Cumulative overhead <1s

---

## Test 5: Related Nodes Performance
**Status**: To be implemented  
**Purpose**: Measure transversal relationship query efficiency

### Relationship Types to Test

**5a: Same Hash Code** (duplicate files)
- Expected results: 2-10 duplicates
- Query complexity: Moderate (hash comparison)

**5b: Same Creation Date**
- Expected results: 10-100 files per date
- Query complexity: High (date extraction + comparison)

**5c: Same Literary Work**
- Expected results: 50-200 related files
- Query complexity: High (work relationship traversal)

**5d: Same Software**
- Expected results: 100-1000 files
- Query complexity: Very high (technical metadata traversal)

**Metrics for each**:
- Relationship query time
- Number of related nodes found
- Path reconstruction time (for multiple nodes)
- Tree expansion time
- Highlighting operation time

**Expected**:
- Query time: 200-2000ms depending on complexity
- Path reconstruction: 500-3000ms for 100 nodes
- Still interactive and usable

---

## Test 6: Cache Effectiveness
**Status**: To be implemented
**Purpose**: Validate cache improves performance and doesn't leak memory

### Sub-Test 6a: Cache Hit Benefit

**Procedure**:
1. Expand node (cache miss - measure time)
2. Collapse node
3. Re-expand node (cache hit - measure time)

**Expected**:
- First expansion: 50-200ms (query + render)
- Second expansion: <5ms (cache retrieval only)
- **Speedup: 10-40x**

### Sub-Test 6b: Cache Growth Pattern

**Procedure**:
- Expand 10, 20, 50, 100 nodes
- Measure cache size and memory after each

**Expected**:
- Cache grows linearly with expansions
- Memory bounded (no leaks)
- Cache size proportional to expanded nodes only

### Sub-Test 6c: Cache vs Full Tree Memory

**Comparison**:
- Full tree (5000 nodes): ~10MB
- Lazy tree + cache (50 expansions): ~200KB
- **Memory savings: 50x**

---

## Test 7: Sustained Load / Stress Testing
**Status**: To be implemented
**Purpose**: Ensure performance doesn't degrade over extended use

### Sub-Test 7a: Sequential Operations

**Scenario**: 100 consecutive operations
- 40 expansions
- 20 searches  
- 20 filter toggles
- 10 sort changes
- 10 related node queries

**Measurements**:
- Performance of operation #1 vs #100
- Memory growth over time
- Response time consistency

**Expected**: <10% performance degradation, bounded memory

### Sub-Test 7b: Memory Stability

**Procedure**:
- Run for 10 minutes of continuous interaction
- Monitor memory with Chrome DevTools
- Check for memory leaks

**Expected**: Memory stabilizes after initial operations, no continuous growth

---

## Implementation Priorities

### Critical for Paper (Implement First):
1. ✅ Test 1: Initial Loading
2. ⭐ Test 2: Node Expansion (depth independence is key claim)
3. ⭐ Test 3: Search Performance (major feature)

### Important Supporting Evidence:
4. Test 5: Related Nodes (demonstrates transversal relationships)
5. Test 4: Filter/Sort (shows query optimization)

### Nice to Have:
6. Test 6: Cache Effectiveness
7. Test 7: Sustained Load

---

## Technical Implementation Notes

### Required Component Enhancements

**For Expansion Testing**:
```typescript
// Add to SemanticTreeAdvanced
private trackExpansion(node: TreeNode, startTime: number) {
  const depth = this.calculateNodeDepth(node);
  // Emit metric with depth information
}
```

**For Search Testing**:
```typescript
// Already partially implemented
// Need to expose:
// - Path reconstruction timing
// - Tree filtering timing
// - Number of paths loaded
```

**For Automated Testing**:
```typescript
// Add programmatic control
interface TestController {
  expandNode(iri: string): Promise<void>;
  search(term: string): Promise<number>;
  applyFilter(label: string): Promise<void>;
  measureCacheSize(): number;
}
```

### Data Requirements

**Need to identify specific test nodes**:
- Nodes at each depth level (1-18)
- Nodes with specific child counts
- Search terms with known result counts
- Nodes with known related nodes

**Solution**: Create a test node registry:
```typescript
const TEST_NODES = {
  depth1: 'http://ficlit.unibo.it/ArchivioEvangelisti/RS1_RS1',
  depth5: 'http://ficlit.unibo.it/.../folder_depth5',
  // etc.
  children10: 'http://...',
  children50: 'http://...',
  // etc.
};
```

---

## Expected Paper Contributions

These tests will provide:

**Quantitative Evidence**:
- Performance scaling curves (O(1) vs O(n²))
- Exact timing measurements
- Memory consumption data
- Speedup ratios at scale

**Validation of Claims**:
- ✓ Progressive loading maintains bounded memory
- ✓ Expansion time independent of depth
- ✓ Search remains interactive even with 1000+ results
- ✓ Filters don't require full tree reload
- ✓ Cache provides significant performance benefit

**Data for Paper Tables**:
- Table 1: Initial Loading Performance Comparison
- Table 2: Expansion Time by Depth
- Table 3: Search Performance by Result Count
- Table 4: Filter/Sort Operation Timings
- Table 5: Related Nodes Query Performance

---

## Next Steps

1. Implement Test 2 (Node Expansion) - Most critical
2. Add depth calculation to component
3. Add programmatic expansion triggering
4. Create expansion_tests.html page
5. Run tests and collect data
6. Document findings

Ready to proceed?
