module Jekyll
  class CategoriesGenerator < Generator
    safe true
    priority :high

    def generate(site)
      all_categories = Set.new

      site.posts.docs.each do |post|
        path = []
        post.data['categories'].each do |cat|
          path << cat
          all_categories.add(path.dup)
        end
      end

      all_categories.each do |category_path|
        site.pages << CategoryPage.new(site, category_path)
      end
    end
  end

  class CategoryPage < Page
    def initialize(site, category_path)
      @site = site
      @base = site.source
      @dir  = category_path.join('/')
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'category.html')

      self.data['category'] = category_path.last
      self.data['categories'] = category_path
      self.data['title'] = category_path.join(' / ')
      self.data['url'] = "/#{@dir}/"
    end
  end
end
