# Performance Testing Framework for Semantic Tree Advanced

## Overview

This testing framework provides a comprehensive comparison between **Monolithic Loading** (basic tree) and **Lazy Loading** (advanced tree) strategies for hierarchical data visualization. The goal is to demonstrate the scalability advantages of the lazy loading approach as described in the research paper.

## Accessing the Test Page

Navigate to: `http://localhost:10214/resource/performance_tests`

## Test Objectives

### Primary Goal
Demonstrate that **lazy loading performance scales constantly** (O(1)) regardless of dataset size, while **monolithic loading degrades exponentially/polynomially** (O(n²) or worse) as the number of nodes increases.

### Key Metrics Measured

1. **Load Time**: Total time from query start to render completion
2. **Query Time**: SPARQL query execution time
3. **Render Time**: DOM rendering and tree construction time
4. **Node Count**: Number of nodes loaded into memory
5. **Memory Estimate**: Approximate memory consumption
6. **Cache Size**: (Lazy only) Number of cached expansions

## Test Scenarios

### Scenario 1: Single Test Run
**Purpose**: Quick verification of a specific dataset size

**Steps**:
1. Select dataset size from dropdown (10 to 5,000 nodes)
2. Click "Run Single Test"
3. Observe side-by-side comparison
4. Review metrics in both panels

**Expected Results**:
- Monolithic: Load time increases significantly with size
- Lazy: Load time remains nearly constant (~40-60ms)

### Scenario 2: Complete Test Suite
**Purpose**: Generate comprehensive performance curves

**Steps**:
1. Click "Run All Tests"
2. Wait for all 8 test sizes to complete (10, 50, 100, 250, 500, 1K, 2.5K, 5K)
3. Review the performance chart
4. Examine the aggregate results table
5. Read the complexity analysis

**Expected Results**:
- **Chart**: Red line (monolithic) curves upward exponentially; Green line (lazy) stays flat
- **Table**: Speedup ratio increases dramatically with size
- **Complexity Analysis**: 
  - Monolithic: O(n²) or higher with "Poor scalability"
  - Lazy: O(1) with "Excellent scalability"

### Scenario 3: Custom Test Sequence
**Purpose**: Focus on specific size ranges

**Recommendations**:
- **Small Scale** (10-100): Baseline comparison
- **Medium Scale** (250-1K): Where monolithic starts degrading
- **Large Scale** (2.5K-5K): Where monolithic becomes impractical

## Interpreting Results

### Performance Chart
- **X-axis**: Dataset size (nodes)
- **Y-axis**: Load time (milliseconds)
- **Monolithic (Red)**: Should show exponential/polynomial growth
- **Lazy (Green)**: Should show flat/constant line

### Aggregate Results Table

| Column | Description |
|--------|-------------|
| Dataset Size | Number of nodes in test |
| Monolithic (ms) | Total load time for monolithic approach |
| Lazy (ms) | Total load time for lazy approach |
| Speedup | Ratio showing how much faster lazy is |
| Winner | Visual indicator of which approach performed better |

**Key Observations to Look For**:
- Speedup should increase with dataset size
- At 5,000 nodes, expect 50x-100x speedup
- Lazy winner badge should appear in all rows

### Complexity Analysis

Automatically calculated after "Run All Tests":

**Growth Rate**: Logarithmic measure of performance scaling
- < 0.3: Constant time O(1)
- 0.3-0.8: Logarithmic O(log n)
- 0.8-1.3: Linear O(n)
- 1.3-2.2: Linearithmic O(n log n)
- \> 2.2: Polynomial/Exponential O(n²+)

## Exporting Results

Click "📊 Export CSV" to download results including:
- All timing measurements
- Memory estimates
- Speedup calculations
- Complexity classifications

**Use Cases for Export**:
- Include in research paper appendix
- Create custom visualizations
- Statistical analysis in R/Python
- Performance documentation

## Understanding the Simulation

**Important**: Currently, the test page uses **simulated** performance data based on theoretical complexity models:

### Monolithic Simulation
- **Query Time**: `50 + (nodeCount/10)²` ms (quadratic growth)
- **Render Time**: `20 + nodeCount*0.5` ms (linear growth)
- **Total**: Combines to show O(n²) behavior

### Lazy Simulation
- **Query Time**: `30-50` ms (constant, slight randomness)
- **Render Time**: `15-25` ms (constant for 3 root nodes)
- **Total**: Shows O(1) behavior

## Next Steps: Real Component Integration

To test with **actual components** instead of simulations:

### Required Modifications

1. **Add Performance Tracking to SemanticTreeAdvanced.ts**
```typescript
interface PerformanceMetrics {
  loadStartTime: number;
  loadEndTime: number;
  queryDuration: number;
  renderDuration: number;
  nodeCount: number;
  cacheSize: number;
}

// Add prop
onPerformanceData?: (metrics: PerformanceMetrics) => void;
```

2. **Instrument Key Methods**
- Track `loadData()` timing
- Track `processSparqlResult()` timing  
- Track `expandNode()` timing
- Emit metrics via callback

3. **Update Test Page**
- Replace simulation functions with actual component instantiation
- Wire up performance callbacks
- Use real SPARQL queries with LIMIT clause

## Test Variations for Paper

### Test 1: Initial Loading Performance
**Varies**: Dataset size (100, 500, 1K, 2.5K, 5K, 10K nodes)
**Measures**: Initial load time, memory footprint
**Expected**: Exponential vs constant

### Test 2: Node Expansion Performance
**Varies**: Hierarchy depth (1, 5, 10, 15, 18 levels)
**Measures**: Expansion time at each depth
**Expected**: Lazy expansion remains bounded

### Test 3: Search Operation Performance
**Varies**: Result set sizes (1, 10, 100, 1000 matches)
**Measures**: Search query time, tree filtering time
**Expected**: Lazy filtering more efficient

### Test 4: Memory Consumption
**Varies**: Dataset size and interaction patterns
**Measures**: DOM nodes, cache size, memory usage
**Expected**: Lazy uses fraction of monolithic memory

## Recommended Testing Protocol

1. **Warm-up**: Run 1-2 tests to initialize browser caching
2. **Baseline**: Run small dataset (10 nodes) for reference
3. **Incremental**: Test each size in sequence
4. **Cool-down**: Wait 1-2 seconds between tests
5. **Repetition**: Run suite 3 times, average results
6. **Documentation**: Export CSV and screenshot chart

## Troubleshooting

### Issue: Chart not displaying
**Solution**: Ensure Chart.js CDN is accessible

### Issue: Tests complete too quickly
**Solution**: This is normal for simulation; real component will take longer

### Issue: No complexity analysis shown
**Solution**: Need at least 3 test results; run more tests

### Issue: Export button not working
**Solution**: Check browser's download permissions

## Future Enhancements

1. **Real-time monitoring**: Track performance during user interaction
2. **Memory profiling**: Use Chrome DevTools Performance API
3. **Network analysis**: Measure SPARQL endpoint response times
4. **Comparative visualizations**: Multiple chart types (bar, scatter, heatmap)
5. **Statistical analysis**: Standard deviation, confidence intervals
6. **Automated testing**: Selenium/Playwright for regression testing

## Contact

For questions about the testing framework or results interpretation, please contact the development team.
