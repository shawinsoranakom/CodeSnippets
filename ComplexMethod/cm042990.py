async def test_complex_dom_manipulation(crawler_strategy):
    js_code = """
    // Create a complex structure
    const container = document.createElement('div');
    container.className = 'test-container';

    const list = document.createElement('ul');
    list.className = 'test-list';

    for (let i = 1; i <= 3; i++) {
        const item = document.createElement('li');
        item.textContent = `Item ${i}`;
        item.className = `item-${i}`;
        list.appendChild(item);
    }

    container.appendChild(list);
    document.body.appendChild(container);
    """
    config = CrawlerRunConfig(js_code=js_code)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'class="test-container"' in response.html
    assert 'class="test-list"' in response.html
    assert 'class="item-1"' in response.html
    assert '>Item 1<' in response.html
    assert '>Item 2<' in response.html
    assert '>Item 3<' in response.html